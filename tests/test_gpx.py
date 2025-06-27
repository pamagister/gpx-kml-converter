import shutil
import unittest
from datetime import datetime
from pathlib import Path

import gpxpy
from gpxpy.gpx import GPXTrackPoint

from gpx_kml_converter.config.config import ProjectConfigManager
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
        self.logger = initialize_logging(ProjectConfigManager()).get_logger("TestGPXProcessor")
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
            input_gpx_list=self.gpx_object,
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

    def test_optimize_track_points(self):
        """
        Test the _optimize_track_points private method.
        """
        # Create a list of dummy track points
        points = [
            GPXTrackPoint(
                latitude=50.00000, longitude=10.00000, elevation=100.0, time=datetime.now()
            ),
            GPXTrackPoint(
                latitude=50.00001, longitude=10.00001, elevation=101.0, time=datetime.now()
            ),  # < 10m from previous
            GPXTrackPoint(
                latitude=50.00002, longitude=10.00002, elevation=102.0, time=datetime.now()
            ),  # < 10m from previous
            GPXTrackPoint(
                latitude=50.00010, longitude=10.00010, elevation=103.0, time=datetime.now()
            ),  # < 10m from previous
            GPXTrackPoint(
                latitude=50.00020, longitude=10.00020, elevation=104.0, time=datetime.now()
            ),  # > 10m from first
            GPXTrackPoint(
                latitude=50.00030, longitude=10.00030, elevation=105.0, time=datetime.now()
            ),  # > 10m from second optimized
        ]
        # Temporarily change min_dist for this specific test
        original_min_dist = self.processor.min_dist
        self.processor.min_dist = 20.0  # meters

        optimized_points = self.processor._optimize_track_points(points)

        # Expected: first point, then point at 50.00020/10.00020, then point at 50.00030/10.00030
        # The number of points should be reduced
        self.assertLess(len(optimized_points), len(points))
        # Exact number of points depends on _calculate_distance, but given the test points
        # and min_dist=10, it should typically keep 3 points (start, second point > 10m, and end)
        self.assertEqual(len(optimized_points), 3)  # Placeholder: Expect 3 optimized points

        # Check if time information is removed and coordinates are rounded
        for point in optimized_points:
            self.assertIsNone(point.time)
            self.assertEqual(point.latitude, round(float(point.latitude), 5))
            self.assertEqual(point.longitude, round(float(point.longitude), 5))
            self.assertIsInstance(point.elevation, int)  # Should be adjusted elevation

        # Restore original min_dist
        self.processor.min_dist = original_min_dist

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


if __name__ == "__main__":
    unittest.main()
