import unittest
from pathlib import Path

from gpxpy.gpx import GPX

from gpx_kml_converter.gui.gui import MainGui


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
