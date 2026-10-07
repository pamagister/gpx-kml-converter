import shutil
import tempfile
import unittest
import zipfile
from datetime import datetime
from pathlib import Path

import gpxpy
from gpxpy.gpx import (
    GPXRoute,
    GPXTrack,
    GPXTrackPoint,
    GPXTrackSegment,
    GPXWaypoint,
)

from gpx_kml_converter.config.config import ConfigParameterManager
from gpx_kml_converter.core.logging import initialize_logging
from src.gpx_kml_converter.core.base import BaseGPXProcessor, GeoFileManager


class TestGPXProcessor(unittest.TestCase):
    """
    Unit tests for the BaseGPXProcessor class using kuhkopfsteig.gpx.
    """

    def setUp(self):
        """
        Set up test environment: define paths and create a temporary output directory.
        """
        # Get the directory of the current test file (e.g., C:/dev/gpx-kml-converter/tests)
        current_test_file_dir = Path(__file__).parent

        self.test_gpx_file = current_test_file_dir.parent / "examples" / "kuhkopfsteig.gpx"
        project_root = current_test_file_dir.parent.parent
        self.output_dir = project_root / "test_output"
        # Ensure the output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = initialize_logging(ConfigParameterManager()).get_logger("TestGPXProcessor")
        self.geo_file_manager = GeoFileManager(logger=self.logger)
        gpx_objects = self.geo_file_manager.load_files(
            [
                self.test_gpx_file,
            ]
        )
        self.gpx_object = [
            gpx_objects.get(self.test_gpx_file),
        ]
        self.processor = BaseGPXProcessor(
            input_=self.gpx_object,
            output=str(self.output_dir),
            logger=self.logger,
        )

    def tearDown(self):
        """
        Clean up test environment: remove the temporary output directory.
        """
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        # Clean up any temporary extraction directories created by _extract_gpx_from_zip
        temp_extract_dir = Path.cwd() / "temp_gpx_extract"
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir)

    def test_get_adjusted_elevation(self):
        """
        Test the _get_adjusted_elevation private method.
        This method relies on srtm data, so we can't mock it easily
        without significant setup. We'll test with a known point and expect
        a rounded float output. The exact value will depend on SRTM data.
        """
        # Create a dummy point for testing
        test_point = GPXTrackPoint(latitude=50.91605, longitude=14.07259, elevation=100.0)
        adjusted_elevation = self.processor._get_adjusted_elevation(test_point)

        self.assertIsInstance(adjusted_elevation, int)
        # Assuming SRTM data is available and provides a value, it should be around 330-350m
        self.assertGreater(
            adjusted_elevation, 124
        )  # Placeholder: Expect elevation to be adjusted, e.g., > 300m
        self.assertLess(
            adjusted_elevation, 400
        )  # Placeholder: Expect elevation to be adjusted, e.g., < 400m
        self.assertNotEqual(adjusted_elevation, 100.0)  # Should be adjusted from original

        # Test point with no initial elevation
        test_point_no_elevation = GPXTrackPoint(latitude=50.91605, longitude=14.07259)
        adjusted_elevation_no_initial = self.processor._get_adjusted_elevation(
            test_point_no_elevation
        )
        self.assertIsInstance(adjusted_elevation_no_initial, int)
        self.assertGreater(adjusted_elevation_no_initial, 124)
        self.assertLess(adjusted_elevation_no_initial, 400)

    def test_calculate_distance(self):
        """
        Test the _calculate_distance private method.
        """
        # Points from Kuhkopfsteig, roughly 100m apart
        point1 = GPXTrackPoint(latitude=50.91605, longitude=14.07259)
        point2 = GPXTrackPoint(latitude=50.91695, longitude=14.07360)
        distance = self.processor._calculate_distance(point1, point2)
        self.assertAlmostEqual(
            distance, 122.59003627960, delta=1
        )  # Placeholder: Expect roughly 100m distance

        # Same point, distance should be 0
        point_same = GPXTrackPoint(latitude=50.0, longitude=10.0)
        distance_same = self.processor._calculate_distance(point_same, point_same)
        self.assertAlmostEqual(distance_same, 0.0)

    def test_douglas_peucker_respects_tolerance_and_preserves_input(self):
        points = [
            GPXTrackPoint(latitude=50.0, longitude=10.0, time=datetime.now()),
            GPXTrackPoint(latitude=50.00015, longitude=10.0005, time=datetime.now()),
            GPXTrackPoint(latitude=50.0, longitude=10.001, time=datetime.now()),
        ]
        self.processor.tolerance = 10
        simplified = self.processor._douglas_peucker(points)
        self.assertEqual(len(simplified), 3)
        self.assertIsNot(simplified[0], points[0])
        self.assertIsNotNone(points[0].time)

        self.processor.tolerance = 20
        simplified = self.processor._douglas_peucker(points)
        self.assertEqual(len(simplified), 2)
        self.assertEqual(simplified[0].latitude, points[0].latitude)
        self.assertEqual(simplified[-1].longitude, points[-1].longitude)

    def test_zero_tolerance_preserves_all_points(self):
        points = [
            GPXTrackPoint(latitude=50.0, longitude=10.0),
            GPXTrackPoint(latitude=50.0001, longitude=10.0001),
            GPXTrackPoint(latitude=50.0002, longitude=10.0002),
        ]
        self.processor.tolerance = 0
        self.assertEqual(len(self.processor._douglas_peucker(points)), len(points))

    def test_compress_files_writes_simplified_gpx(self):
        self.processor.include_elevation = False
        self.processor.tolerance = 10

        result = self.processor.compress_files()

        self.assertEqual(len(result), 1)
        output_path = next(iter(result))
        self.assertTrue(output_path.exists())
        optimized_gpx = gpxpy.parse(open(output_path, "r", encoding="utf-8"))
        original_point_count = sum(
            len(segment.points) for track in self.gpx_object[0].tracks for segment in track.segments
        )
        optimized_point_count = sum(
            len(segment.points) for track in optimized_gpx.tracks for segment in track.segments
        )
        self.assertLess(optimized_point_count, original_point_count)

    def test_merge_files_preserves_all_gpx_descriptions(self):
        source = gpxpy.gpx.GPX()
        source.waypoints.append(
            GPXWaypoint(
                latitude=50.0,
                longitude=10.0,
                name="Waypoint",
                description="Waypoint description",
            )
        )

        track = GPXTrack(name="Track", description="Track description")
        track_segment = GPXTrackSegment()
        track_segment.points.append(GPXTrackPoint(latitude=50.0, longitude=10.0))
        track_point = GPXTrackPoint(latitude=50.0001, longitude=10.0001)
        track_point.description = "Track point description"
        track_segment.points.append(track_point)
        track_segment.points.append(GPXTrackPoint(latitude=50.0002, longitude=10.0002))
        track.segments.append(track_segment)
        source.tracks.append(track)

        route = GPXRoute(name="Route", description="Route description")
        route_point = GPXTrackPoint(latitude=50.1, longitude=10.1)
        route_point.description = "Route point description"
        route.points.append(route_point)
        source.routes.append(route)

        self.processor.input = [source]
        self.processor.include_elevation = False
        self.processor.tolerance = 1000
        merged_gpx = next(iter(self.processor.merge_files().values()))

        self.assertEqual(merged_gpx.waypoints[0].description, "Waypoint description")
        self.assertEqual(merged_gpx.tracks[0].description, "Track description")
        self.assertEqual(
            merged_gpx.tracks[0].segments[0].points[0].description,
            None,
        )
        self.assertEqual(
            len(merged_gpx.tracks[0].segments[0].points),
            3,
        )
        self.assertEqual(
            merged_gpx.tracks[0].segments[0].points[1].description,
            "Track point description",
        )
        self.assertEqual(merged_gpx.routes[0].description, "Route description")
        self.assertEqual(merged_gpx.routes[0].points[0].description, "Route point description")

    def test_save_gpx_file(self):
        """
        Test the _save_gpx_file private method.
        """
        gpx_obj = gpxpy.gpx.GPX()
        gpx_obj.name = "Test Save"
        output_path = self.output_dir / "saved_test.gpx"

        self.processor._save_gpx_file(gpx_obj, output_path)
        self.assertTrue(output_path.exists())

        # Verify content by reloading
        reloaded_gpx = gpxpy.parse(open(output_path, "r", encoding="utf-8"))
        self.assertEqual(reloaded_gpx.name, "Test Save")

    def test_load_files_keeps_same_named_files_from_separate_archives(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archives = [root / "first.zip", root / "second.zip"]
            for archive in archives:
                with zipfile.ZipFile(archive, "w") as zip_file:
                    zip_file.write(self.test_gpx_file, "tracks/shared.gpx")

            loaded = self.geo_file_manager.load_files(archives)

        self.assertEqual(len(loaded), 2)


if __name__ == "__main__":
    unittest.main()
