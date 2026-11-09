import logging
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from tkinter import messagebox

from gpxpy.gpx import GPX, GPXRoute, GPXTrack, GPXWaypoint

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


class _FakeVariable:
    def __init__(self, value=""):
        self.value = value

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class _FakeProgress:
    def __init__(self):
        self.value = None

    def configure(self, **kwargs):
        self.value = kwargs.get("value")

    def stop(self):
        pass


class _FakeConfigParam:
    def __init__(self, value):
        self.value = value


class _FakeConfigCli:
    output = _FakeConfigParam("/tmp/out")
    tolerance = _FakeConfigParam(10.0)
    elevation = _FakeConfigParam(False)


class _FakeConfigApp:
    date_format = _FakeConfigParam("%Y-%m-%d")


class _FakeConfigManager:
    """Minimal stand-in providing the config attributes _run_processing reads."""

    cli = _FakeConfigCli()
    app = _FakeConfigApp()


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

    def test_category_removal_mutates_source_in_place_without_generated_copy(self):
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
            gui._show_empty_inspector = lambda: None

            def rebuild_tree():
                pass

            gui._rebuild_artifact_tree = rebuild_tree

            result = gui._delete_selected_workspace_items()

            self.assertEqual(result, "break")
            self.assertEqual(len(source_gpx.waypoints), 0)
            self.assertEqual(gui.gpx_output, {})
            self.assertEqual(source_path.read_bytes(), original_contents)

    def test_removal_of_two_input_files(self):
        with TemporaryDirectory() as temp_dir:
            path_a = Path(temp_dir) / "a.gpx"
            path_b = Path(temp_dir) / "b.gpx"
            gpx_a = GPX()
            gpx_b = GPX()
            path_a.write_text(gpx_a.to_xml(), encoding="utf-8")
            path_b.write_text(gpx_b.to_xml(), encoding="utf-8")
            gui = MainGui.__new__(MainGui)
            gui.artifact_tree = SelectedItems("file_a", "file_b")
            gui._tree_identity = {
                "file_a": ArtifactIdentity("input", path_a, "file"),
                "file_b": ArtifactIdentity("input", path_b, "file"),
            }
            gui._tree_group_identity = {}
            gui.gpx_input = {path_a: gpx_a, path_b: gpx_b}
            gui.gpx_output = {}
            gui._file_summaries = {}
            gui._file_origins = {
                ("input", path_a): FileOrigin(path_a),
                ("input", path_b): FileOrigin(path_b),
            }
            gui._file_labels = {}
            gui._virtual_files = set()
            gui._identity_tree_item = {}
            gui.logger = logging.getLogger(__name__)
            gui._on_browser_selection = lambda: None
            gui._show_empty_inspector = lambda: None

            def rebuild_tree():
                pass

            gui._rebuild_artifact_tree = rebuild_tree

            result = gui._delete_selected_workspace_items()

            self.assertEqual(result, "break")
            self.assertNotIn(path_a, gui.gpx_input)
            self.assertNotIn(path_b, gui.gpx_input)
            self.assertEqual(gui.gpx_output, {})

    def test_removal_across_mixed_artifacts_and_multiple_files(self):
        with TemporaryDirectory() as temp_dir:
            path_a = Path(temp_dir) / "a.gpx"
            path_b = Path(temp_dir) / "b.gpx"
            gpx_a = GPX()
            gpx_a.waypoints.append(GPXWaypoint(latitude=50.0, longitude=10.0, name="WP A"))
            gpx_a.tracks.append(GPXTrack(name="Track A"))
            gpx_b = GPX()
            gpx_b.waypoints.append(GPXWaypoint(latitude=51.0, longitude=11.0, name="WP B"))
            gpx_b.routes.append(GPXRoute(name="Route B"))
            path_a.write_text(gpx_a.to_xml(), encoding="utf-8")
            path_b.write_text(gpx_b.to_xml(), encoding="utf-8")
            gui = MainGui.__new__(MainGui)
            gui.artifact_tree = SelectedItems("wp_a", "track_a", "wp_b", "route_b")
            gui._tree_identity = {
                "wp_a": ArtifactIdentity("input", path_a, "waypoint", 0),
                "track_a": ArtifactIdentity("input", path_a, "track", 0),
                "wp_b": ArtifactIdentity("input", path_b, "waypoint", 0),
                "route_b": ArtifactIdentity("input", path_b, "route", 0),
            }
            gui._tree_group_identity = {}
            gui.gpx_input = {path_a: gpx_a, path_b: gpx_b}
            gui.gpx_output = {}
            gui._file_summaries = {}
            gui._file_origins = {
                ("input", path_a): FileOrigin(path_a),
                ("input", path_b): FileOrigin(path_b),
            }
            gui._file_labels = {}
            gui._virtual_files = set()
            gui._identity_tree_item = {}
            gui.logger = logging.getLogger(__name__)
            gui._on_browser_selection = lambda: None
            gui._show_empty_inspector = lambda: None

            def rebuild_tree():
                pass

            gui._rebuild_artifact_tree = rebuild_tree

            result = gui._delete_selected_workspace_items()

            self.assertEqual(result, "break")
            self.assertEqual(len(gpx_a.waypoints), 0)
            self.assertEqual(len(gpx_a.tracks), 0)
            self.assertEqual(len(gpx_b.waypoints), 0)
            self.assertEqual(len(gpx_b.routes), 0)
            self.assertEqual(gui.gpx_output, {})

    def test_processing_summary_shows_count_mode_and_output_dir(self):
        gui = MainGui.__new__(MainGui)
        gui.summary_var = _FakeVariable()
        gui.summary_path_var = _FakeVariable()
        gui._last_output_dir = None
        gui.logger = logging.getLogger(__name__)

        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "out"
            output_dir.mkdir()
            output_file = output_dir / "result.gpx"
            output_file.write_text("gpx", encoding="utf-8")
            output_map = {output_file: GPX()}

            gui._show_processing_summary(3, "Compress Files", output_map)

            self.assertIn("3 file(s)", gui.summary_var.get())
            self.assertIn("Compress Files", gui.summary_var.get())
            self.assertEqual(gui._last_output_dir, output_dir)
            self.assertEqual(gui.summary_path_var.get(), str(output_dir))

    def test_processing_summary_multiple_output_dirs_stores_none(self):
        gui = MainGui.__new__(MainGui)
        gui.summary_var = _FakeVariable()
        gui.summary_path_var = _FakeVariable()
        gui._last_output_dir = None
        gui.logger = logging.getLogger(__name__)

        with TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "sub").mkdir()
            output_map = {
                Path(temp_dir) / "a.gpx": GPX(),
                Path(temp_dir) / "sub" / "b.gpx": GPX(),
            }
            gui._show_processing_summary(2, "Merge Files", output_map)

            self.assertIsNone(gui._last_output_dir)
            self.assertEqual(gui.summary_path_var.get(), "")

    def test_processing_error_shown_non_blockingly(self):
        gui = MainGui.__new__(MainGui)
        gui.summary_var = _FakeVariable()
        gui.summary_path_var = _FakeVariable()
        gui.current_file_var = _FakeVariable()
        gui.progress = _FakeProgress()
        gui.logger = logging.getLogger(__name__)

        gui._show_processing_error(ValueError("boom"), "Compress Files", 2)

        self.assertEqual(gui.progress.value, 0)
        self.assertIn("Error", gui.current_file_var.get())
        self.assertIn("Processing failed", gui.summary_var.get())

    def test_clear_workspace_requires_confirmation(self):
        gui = MainGui.__new__(MainGui)
        gui.gpx_input = {Path("a.gpx"): GPX()}
        gui.gpx_output = {Path("b.gpx"): GPX()}
        gui._file_summaries = {}
        gui._file_origins = {}
        gui._file_labels = {}
        gui._virtual_files = set()
        gui.logger = logging.getLogger(__name__)
        gui._rebuild_artifact_tree = lambda: None
        gui._show_empty_inspector = lambda: None

        cleared = []

        def askyesno(title, message, **kwargs):
            cleared.append(True)
            return False

        messagebox_askyesno = messagebox.askyesno
        try:
            messagebox.askyesno = askyesno
            gui._clear_files()
        finally:
            messagebox.askyesno = messagebox_askyesno

        # Cancellation leaves the workspace unchanged
        self.assertIn(Path("a.gpx"), gui.gpx_input)
        self.assertIn(Path("b.gpx"), gui.gpx_output)
        self.assertEqual(cleared, [True])

    def test_clear_workspace_clears_after_confirmation(self):
        gui = MainGui.__new__(MainGui)
        gui.gpx_input = {Path("a.gpx"): GPX()}
        gui.gpx_output = {Path("b.gpx"): GPX()}
        gui._file_summaries = {}
        gui._file_origins = {}
        gui._file_labels = {}
        gui._virtual_files = set()
        gui.logger = logging.getLogger(__name__)
        gui._rebuild_artifact_tree = lambda: None
        gui._show_empty_inspector = lambda: None

        def askyesno(title, message, **kwargs):
            return True

        messagebox_askyesno = messagebox.askyesno
        try:
            messagebox.askyesno = askyesno
            gui._clear_files()
        finally:
            messagebox.askyesno = messagebox_askyesno

        self.assertEqual(gui.gpx_input, {})
        self.assertEqual(gui.gpx_output, {})

    def test_undo_last_removal_restores_workspace(self):
        path_a = Path("a.gpx")
        path_b = Path("b.gpx")
        gpx_a, gpx_b = GPX(), GPX()
        gui = MainGui.__new__(MainGui)
        gui.artifact_tree = SelectedItems("file_a")
        gui._tree_identity = {"file_a": ArtifactIdentity("input", path_a, "file")}
        gui._tree_group_identity = {}
        gui.gpx_input = {path_a: gpx_a, path_b: gpx_b}
        gui.gpx_output = {}
        gui._file_summaries = {}
        gui._file_origins = {}
        gui._file_labels = {}
        gui._virtual_files = set()
        gui._identity_tree_item = {}
        gui.logger = logging.getLogger(__name__)
        gui._rebuild_artifact_tree = lambda: None
        gui._show_empty_inspector = lambda: None

        result = gui._delete_selected_workspace_items()

        self.assertEqual(result, "break")
        self.assertNotIn(path_a, gui.gpx_input)
        self.assertIn(path_b, gui.gpx_input)

        # Undo restores the state before the removal.
        gui._undo_last_removal()

        self.assertIn(path_a, gui.gpx_input)
        self.assertIn(path_b, gui.gpx_input)
        self.assertIsNone(gui._undo_snapshot)

    def test_processing_without_selection_asks_confirmation_and_cancel_aborts(self):
        gui = MainGui.__new__(MainGui)
        gui.gpx_input = {Path("a.gpx"): GPX(), Path("b.gpx"): GPX()}
        gui.gpx_output = {}
        gui._file_summaries = {}
        gui._file_origins = {}
        gui._file_labels = {}
        gui._virtual_files = set()
        gui.logger = logging.getLogger(__name__)
        gui.root = type("R", (), {"after": lambda self, *a, **k: None})()
        gui.config_manager = _FakeConfigManager()
        gui.progress = _FakeProgress()
        gui.current_file_var = _FakeVariable()
        gui.artifact_tree = SelectedItems()
        gui.run_buttons = {}
        gui.clear_files_button = type("B", (), {"config": lambda self, **kw: None})()

        calls = []

        def askyesno(title, message, **kwargs):
            calls.append(message)
            return False

        processed = []

        def fake_process(
            input_files, *, mode, output, tolerance, date_format, elevation, logger, source_origins
        ):
            processed.append(input_files)
            return {}

        import gpx_kml_converter.gui.gui as gui_module

        orig_process = gui_module.process_gpx_files
        gui_module.process_gpx_files = fake_process
        messagebox_askyesno = messagebox.askyesno
        try:
            messagebox.askyesno = askyesno
            gui._run_processing("compress")
        finally:
            gui_module.process_gpx_files = orig_process
            messagebox.askyesno = messagebox_askyesno

        # The confirmation dialog is shown; cancellation aborts processing.
        self.assertEqual(len(calls), 1)
        self.assertIn("none is selected", calls[0])
        self.assertIn("really be processed", calls[0])
        self.assertEqual(processed, [])

    def test_processing_without_selection_confirmed_processes_all(self):
        gui = MainGui.__new__(MainGui)
        gpx_a, gpx_b = GPX(), GPX()
        gui.gpx_input = {Path("a.gpx"): gpx_a, Path("b.gpx"): gpx_b}
        gui.gpx_output = {}
        gui._file_summaries = {}
        gui._file_origins = {}
        gui._file_labels = {}
        gui._virtual_files = set()
        gui.logger = logging.getLogger(__name__)
        gui.root = type("R", (), {"after": lambda self, *a, **k: None})()
        gui.config_manager = _FakeConfigManager()
        gui.progress = _FakeProgress()
        gui.current_file_var = _FakeVariable()
        gui.artifact_tree = SelectedItems()
        gui.run_buttons = {}
        gui.clear_files_button = type("B", (), {"config": lambda self, **kw: None})()

        calls = []

        def askyesno(title, message, **kwargs):
            calls.append(message)
            return True

        processed = []

        def fake_process(
            input_files, *, mode, output, tolerance, date_format, elevation, logger, source_origins
        ):
            processed.append(list(input_files))
            return {}

        import gpx_kml_converter.gui.gui as gui_module

        orig_process = gui_module.process_gpx_files
        gui_module.process_gpx_files = fake_process
        messagebox_askyesno = messagebox.askyesno
        try:
            messagebox.askyesno = askyesno
            gui._run_processing("compress")
        finally:
            gui_module.process_gpx_files = orig_process
            messagebox.askyesno = messagebox_askyesno

        # Wait for the processing thread to complete.
        deadline = time.time() + 5
        while not processed and time.time() < deadline:
            time.sleep(0.05)

        self.assertEqual(len(calls), 1)
        self.assertIn("none is selected", calls[0])
        self.assertEqual(len(processed), 1)
        self.assertEqual(len(processed[0]), 2)


if __name__ == "__main__":
    unittest.main()
