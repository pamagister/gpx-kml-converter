import logging
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from gpxpy.gpx import GPX, GPXWaypoint

from gpx_kml_converter.core.file_loader import FileOrigin
from gpx_kml_converter.gui.artifacts import ArtifactGroupIdentity, ArtifactIdentity
from gpx_kml_converter.gui.gui import MainGui


class SelectedItems:
    def __init__(self, *item_ids):
        self.item_ids = item_ids
        self.focused = None

    def selection(self):
        return self.item_ids

    def selection_set(self, *item_ids):
        self.item_ids = item_ids

    def focus(self, item_id):
        self.focused = item_id

    def see(self, _item_id):
        pass


class TestGuiWorkflow(unittest.TestCase):
    def test_empty_selection_resolves_to_all_loaded_inputs_in_order(self):
        files = {
            Path("first.gpx"): GPX(),
            Path("second.gpx"): GPX(),
            Path("third.gpx"): GPX(),
        }

        self.assertEqual(MainGui._selected_paths(files, ()), list(files))

    def test_explicit_selection_resolves_only_chosen_inputs_in_order(self):
        files = {
            Path("first.gpx"): GPX(),
            Path("second.gpx"): GPX(),
            Path("third.gpx"): GPX(),
        }

        self.assertEqual(
            MainGui._selected_paths(files, (2, 0)),
            [Path("third.gpx"), Path("first.gpx")],
        )

    def test_selected_results_are_added_once_without_removing_them_from_results(self):
        existing_path = Path("existing.gpx")
        result_path = Path("result.gpx")
        existing_gpx = GPX()
        result_gpx = GPX()
        inputs = {existing_path: existing_gpx}
        results = {existing_path: GPX(), result_path: result_gpx}

        added_paths = MainGui._add_results_to_inputs(inputs, results, [existing_path, result_path])

        self.assertEqual(added_paths, [result_path])
        self.assertEqual(list(inputs), [existing_path, result_path])
        self.assertIs(inputs[existing_path], existing_gpx)
        self.assertIs(inputs[result_path], result_gpx)
        self.assertEqual(list(results), [existing_path, result_path])

    def test_removal_accepts_multiselect_only_when_all_nodes_share_a_type(self):
        gui = MainGui.__new__(MainGui)
        gui.artifact_tree = SelectedItems("file", "track")
        gui._tree_identity = {
            "file": ArtifactIdentity("input", Path("source.gpx"), "file"),
            "track": ArtifactIdentity("input", Path("source.gpx"), "track", 0),
        }
        gui._tree_group_identity = {}
        self.assertIsNone(gui._selected_removal_kind())

        gui.artifact_tree = SelectedItems("route", "route-group")
        gui._tree_identity = {"route": ArtifactIdentity("input", Path("source.gpx"), "route", 0)}
        gui._tree_group_identity = {
            "route-group": ArtifactGroupIdentity("output", Path("result.gpx"), "route")
        }
        self.assertEqual(gui._selected_removal_kind(), "route")

    def test_file_removal_only_removes_workspace_entry(self):
        with TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "source.gpx"
            source_path.write_text(GPX().to_xml(), encoding="utf-8")
            original_contents = source_path.read_bytes()
            gui = MainGui.__new__(MainGui)
            gui.artifact_tree = SelectedItems("file")
            gui._tree_identity = {"file": ArtifactIdentity("input", source_path, "file")}
            gui._tree_group_identity = {}
            shared_gpx = GPX()
            gui.gpx_input = {source_path: shared_gpx}
            gui.gpx_output = {source_path: shared_gpx}
            gui._file_summaries = {}
            gui._file_origins = {("input", source_path): FileOrigin(source_path)}
            gui._file_labels = {}
            gui._virtual_files = set()
            gui.logger = logging.getLogger(__name__)
            gui._rebuild_artifact_tree = lambda: None
            gui._show_empty_inspector = lambda: None

            result = gui._delete_selected_workspace_items()

            self.assertEqual(result, "break")
            self.assertNotIn(source_path, gui.gpx_input)
            self.assertNotIn(source_path, gui.gpx_output)
            self.assertEqual(source_path.read_bytes(), original_contents)

    def test_category_removal_creates_generated_copy_without_mutating_source(self):
        with TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "source.gpx"
            source_gpx = GPX()
            source_gpx.waypoints.append(GPXWaypoint(latitude=50.0, longitude=10.0, name="Summit"))
            source_path.write_text(source_gpx.to_xml(), encoding="utf-8")
            original_contents = source_path.read_bytes()
            gui = MainGui.__new__(MainGui)
            gui.artifact_tree = SelectedItems("pois")
            gui._tree_identity = {}
            gui._tree_group_identity = {
                "pois": ArtifactGroupIdentity("input", source_path, "waypoint")
            }
            gui.gpx_input = {source_path: source_gpx}
            gui.gpx_output = {}
            gui._file_summaries = {}
            gui._file_origins = {("input", source_path): FileOrigin(source_path)}
            gui._file_labels = {}
            gui._virtual_files = set()
            gui._working_copy_counter = 0
            gui._identity_tree_item = {}
            gui.logger = logging.getLogger(__name__)
            gui._on_browser_selection = lambda: None

            def rebuild_tree():
                result_path = next(iter(gui.gpx_output))
                gui._identity_tree_item = {
                    ArtifactIdentity("output", result_path, "file"): "result"
                }

            gui._rebuild_artifact_tree = rebuild_tree

            result = gui._delete_selected_workspace_items()

            derived_gpx = next(iter(gui.gpx_output.values()))
            self.assertEqual(result, "break")
            self.assertEqual(len(source_gpx.waypoints), 1)
            self.assertEqual(derived_gpx.waypoints, [])
            self.assertEqual(source_path.read_bytes(), original_contents)
            self.assertEqual(gui.artifact_tree.selection(), ("result",))
