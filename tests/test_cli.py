import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import gpxpy
from gpxpy.gpx import GPX, GPXWaypoint

from gpx_kml_converter.cli.cli import _expand_inputs, main


class TestCli(unittest.TestCase):
    def _run_cli(self, working_directory: Path, args: list[str]) -> int:
        previous_directory = Path.cwd()
        try:
            os.chdir(working_directory)
            return main(args)
        finally:
            os.chdir(previous_directory)

    def test_directory_inputs_are_non_recursive_by_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            direct_file = root / "direct.gpx"
            nested_file = root / "nested" / "nested.kml"
            ignored_file = root / "ignored.txt"
            direct_file.touch()
            nested_file.parent.mkdir()
            nested_file.touch()
            ignored_file.touch()

            direct_inputs = _expand_inputs([str(root)], recursive=False)
            recursive_inputs = _expand_inputs([str(root)], recursive=True)

            self.assertEqual(direct_inputs, [direct_file.resolve()])
            self.assertEqual(recursive_inputs, [direct_file.resolve(), nested_file.resolve()])

    def test_cli_dispatches_merge_for_multiple_inputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            inputs = [Path(temp_dir) / "one.gpx", Path(temp_dir) / "two.kml"]
            for path in inputs:
                path.touch()

            logger_manager = MagicMock()
            loaded_files = {path: object() for path in inputs}

            with (
                patch("gpx_kml_converter.cli.cli.initialize_logging", return_value=logger_manager),
                patch("gpx_kml_converter.cli.cli.GeoFileManager") as file_manager,
                patch("gpx_kml_converter.cli.cli.BaseGPXProcessor") as processor_class,
            ):
                file_manager.return_value.load_files.return_value = loaded_files
                processor_class.return_value.merge_files.return_value = {
                    Path("merged_output.gpx"): object()
                }

                exit_code = main(["--mode", "merge", *(str(path) for path in inputs)])

            self.assertEqual(exit_code, 0)
            processor_class.return_value.merge_files.assert_called_once()
            processor_class.return_value.compress_files.assert_not_called()

    def test_cli_merges_poi_gpx_and_kml_examples(self):
        fixtures_dir = Path(__file__).resolve().parents[1] / "examples" / "POIs"
        gpx_path = fixtures_dir / "beaches.gpx"
        kml_path = fixtures_dir / "more_beaches.kml"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"
            result = self._run_cli(
                Path(temp_dir),
                [
                    "--mode",
                    "merge",
                    "--output",
                    str(output_dir),
                    str(gpx_path),
                    str(kml_path),
                ],
            )

            self.assertEqual(result, 0)
            merged_gpx = gpxpy.parse((output_dir / "merged_output.gpx").read_text(encoding="utf-8"))
            merged_names = [waypoint.name for waypoint in merged_gpx.waypoints]

        self.assertEqual(len(merged_names), 41)
        self.assertIn("Brandinchi Beach", merged_names)
        self.assertIn("Spiaggia La Pelosa", merged_names)
        self.assertIn("La Cinta Beach", merged_names)
        brandinchi = next(
            point for point in merged_gpx.waypoints if point.name == "Brandinchi Beach"
        )
        self.assertIn("Little Tahiti", brandinchi.description)

    def test_cli_merge_preserves_kml_description(self):
        cities_path = Path(__file__).resolve().parents[1] / "examples" / "POIs" / "cities.kml"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"
            result = self._run_cli(
                Path(temp_dir),
                ["--mode", "merge", "--output", str(output_dir), str(cities_path)],
            )
            merged_gpx = gpxpy.parse((output_dir / "merged_output.gpx").read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        olbia = next(point for point in merged_gpx.waypoints if point.name == "Olbia")
        self.assertEqual(olbia.description, "Dies ist eine Beschreibung")

    def test_add_poi_updates_existing_gpx_and_preserves_existing_waypoints(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "waypoints.gpx"
            original = GPX()
            original.waypoints.append(
                GPXWaypoint(latitude=48.8584, longitude=2.2945, name="Eiffel Tower")
            )
            source.write_text(original.to_xml(), encoding="utf-8")

            result = self._run_cli(
                root,
                [
                    "--mode",
                    "add-poi",
                    "--lat",
                    "51.0632",
                    "--lon",
                    "13.7421",
                    "--name",
                    "Historic Cafe",
                    "--desc",
                    "A historic coffee shop.",
                    "--sym",
                    "Coffee",
                    "--ele",
                    "115",
                    str(source),
                ],
            )

            saved_gpx = gpxpy.parse(source.read_text(encoding="utf-8"))
            self.assertEqual(result, 0)
            self.assertEqual(len(saved_gpx.waypoints), 2)
            self.assertEqual(saved_gpx.waypoints[0].name, "Eiffel Tower")
            added_waypoint = saved_gpx.waypoints[1]
            self.assertEqual(added_waypoint.latitude, 51.0632)
            self.assertEqual(added_waypoint.longitude, 13.7421)
            self.assertEqual(added_waypoint.name, "Historic Cafe")
            self.assertEqual(added_waypoint.description, "A historic coffee shop.")
            self.assertEqual(added_waypoint.symbol, "Coffee")
            self.assertEqual(added_waypoint.elevation, 115)

    def test_add_poi_writes_to_output_file_without_changing_input(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.gpx"
            destination = root / "destination.gpx"
            original = GPX()
            original.waypoints.append(
                GPXWaypoint(latitude=48.8584, longitude=2.2945, name="Existing")
            )
            source.write_text(original.to_xml(), encoding="utf-8")
            original_content = source.read_bytes()

            result = self._run_cli(
                root,
                [
                    "--mode",
                    "add-poi",
                    "--lat",
                    "51.0",
                    "--lon",
                    "13.0",
                    "--name",
                    "New POI",
                    "--output",
                    str(destination),
                    str(source),
                ],
            )

            saved_gpx = gpxpy.parse(destination.read_text(encoding="utf-8"))
            self.assertEqual(result, 0)
            self.assertEqual(source.read_bytes(), original_content)
            self.assertEqual([point.name for point in saved_gpx.waypoints], ["Existing", "New POI"])

    def test_add_poi_creates_missing_gpx_and_optional_fields_are_omitted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "new.gpx"

            result = self._run_cli(
                root,
                [
                    "--mode",
                    "add-poi",
                    "--lat",
                    "48.8584",
                    "--lon",
                    "2.2945",
                    "--name",
                    "Eiffel Tower",
                    str(source),
                ],
            )

            created_gpx = gpxpy.parse(source.read_text(encoding="utf-8"))
            self.assertEqual(result, 0)
            self.assertEqual(len(created_gpx.waypoints), 1)
            self.assertEqual(created_gpx.waypoints[0].name, "Eiffel Tower")
            self.assertIsNone(created_gpx.waypoints[0].description)
            self.assertIsNone(created_gpx.waypoints[0].symbol)
            self.assertIsNone(created_gpx.waypoints[0].elevation)

    def test_add_poi_appends_duplicate_waypoints(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "duplicates.gpx"
            original = GPX()
            original.waypoints.append(GPXWaypoint(latitude=51, longitude=13, name="Same POI"))
            source.write_text(original.to_xml(), encoding="utf-8")

            result = self._run_cli(
                root,
                [
                    "--mode",
                    "add-poi",
                    "--lat",
                    "51",
                    "--lon",
                    "13",
                    "--name",
                    "Same POI",
                    str(source),
                ],
            )

            saved_gpx = gpxpy.parse(source.read_text(encoding="utf-8"))
            self.assertEqual(result, 0)
            self.assertEqual(
                [(point.latitude, point.longitude, point.name) for point in saved_gpx.waypoints],
                [(51, 13, "Same POI"), (51, 13, "Same POI")],
            )

    def test_add_poi_rejects_out_of_range_coordinates_without_modifying_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "existing.gpx"
            source.write_text(GPX().to_xml(), encoding="utf-8")
            original_content = source.read_bytes()

            result = self._run_cli(
                root,
                [
                    "--mode",
                    "add-poi",
                    "--lat",
                    "91",
                    "--lon",
                    "13",
                    "--name",
                    "Invalid POI",
                    str(source),
                ],
            )

            self.assertEqual(result, 1)
            self.assertEqual(source.read_bytes(), original_content)

    def test_add_poi_rejects_malformed_gpx_without_overwriting_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "malformed.gpx"
            original_content = b"<gpx><wpt"
            source.write_bytes(original_content)

            result = self._run_cli(
                root,
                [
                    "--mode",
                    "add-poi",
                    "--lat",
                    "51",
                    "--lon",
                    "13",
                    "--name",
                    "POI",
                    str(source),
                ],
            )

            self.assertEqual(result, 1)
            self.assertEqual(source.read_bytes(), original_content)

    def test_add_poi_requires_one_input_file_and_required_fields(self):
        with self.assertRaises(SystemExit):
            main(["--mode", "add-poi", "one.gpx", "two.gpx"])
        with self.assertRaises(SystemExit):
            main(["--mode", "add-poi", "one.gpx"])


if __name__ == "__main__":
    unittest.main()
