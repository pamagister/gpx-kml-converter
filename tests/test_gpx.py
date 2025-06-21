import shutil
import unittest
import zipfile
from datetime import datetime
from pathlib import Path

import gpxpy
from gpxpy.gpx import GPXTrackPoint

from python_template_project.config.config import ConfigParameterManager
from python_template_project.core.logging import initialize_logging
from src.python_template_project.core.base import BaseGPXProcessor


class TestGPXProcessor(unittest.TestCase):
    """
    Unit tests for the BaseGPXProcessor class using kuhkopfsteig.gpx.
    """

    def setUp(self):
        """
        Set up test environment: define paths and create a temporary output directory.
        """
        # Get the directory of the current test file (e.g., C:/dev/python-template-project/tests)
        current_test_file_dir = Path(__file__).parent

        self.test_gpx_file = current_test_file_dir.parent / "examples" / "kuhkopfsteig.gpx"
        project_root = current_test_file_dir.parent.parent
        self.output_dir = project_root / "test_output"
        # Ensure the output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = initialize_logging(ConfigParameterManager()).get_logger("TestGPXProcessor")

        self.processor = BaseGPXProcessor(
            input_=str(self.test_gpx_file),
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

    def test_get_output_folder(self):
        """
        Test the _get_output_folder private method.
        Ensures the output folder is created correctly.
        """
        # Test with a specified output folder
        processor_with_output = BaseGPXProcessor(
            input_=str(self.test_gpx_file),
            output="custom_output",
            logger=self.logger,
        )
        output_path = processor_with_output._get_output_folder()
        self.assertEqual(output_path, Path("custom_output"))
        self.assertTrue(output_path.exists())
        shutil.rmtree(output_path)  # Clean up custom output

        # Test without a specified output folder (default behavior)
        processor_no_output = BaseGPXProcessor(input_=str(self.test_gpx_file), logger=self.logger)
        output_path_default = processor_no_output._get_output_folder()
        # Check if the path starts with 'gpx_processed_' and current date
        self.assertTrue(str(output_path_default).startswith(str(Path.cwd() / "gpx_processed_")))
        self.assertTrue(output_path_default.exists())
        self.assertTrue(output_path_default.is_dir())
        shutil.rmtree(output_path_default)  # Clean up default output

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

    def test_get_input_files(self):
        """
        Test the _get_input_files private method.
        """
        # Test with a single GPX file
        files_single = self.processor._get_input_files()
        self.assertEqual(len(files_single), 1)
        self.assertEqual(files_single[0], self.test_gpx_file)

        # Test with a directory containing GPX files
        temp_dir = self.output_dir / "temp_gpx_dir"
        temp_dir.mkdir()
        (temp_dir / "test1.gpx").touch()
        (temp_dir / "test2.gpx").touch()
        (temp_dir / "not_gpx.txt").touch()

        processor_dir = BaseGPXProcessor(input_=str(temp_dir), logger=self.logger)
        files_dir = processor_dir._get_input_files()
        self.assertEqual(len(files_dir), 2)
        self.assertTrue(any(f.name == "test1.gpx" for f in files_dir))
        self.assertTrue(any(f.name == "test2.gpx" for f in files_dir))

        # Test with a zip file (will create temp_gpx_extract)
        temp_zip_file = self.output_dir / "test.zip"
        with zipfile.ZipFile(temp_zip_file, "w") as zf:
            zf.writestr("zip_gpx_1.gpx", "<gpx></gpx>")
            zf.writestr("zip_gpx_2.gpx", "<gpx></gpx>")
            zf.writestr("not_gpx_in_zip.txt", "text")

        processor_zip = BaseGPXProcessor(input_=str(temp_zip_file), logger=self.logger)
        files_zip = processor_zip._get_input_files()
        self.assertEqual(len(files_zip), 2)
        self.assertTrue(any(f.name == "zip_gpx_1.gpx" for f in files_zip))
        self.assertTrue(any(f.name == "zip_gpx_2.gpx" for f in files_zip))

    def test_load_gpx_file(self):
        """
        Test the _load_gpx_file private method.
        """
        gpx_obj = self.processor._load_gpx_file(self.test_gpx_file)
        self.assertIsNotNone(gpx_obj)
        self.assertIsInstance(gpx_obj, gpxpy.gpx.GPX)
        self.assertGreater(len(gpx_obj.tracks), 0)  # Kuhkopfsteig has tracks

        # Test with a non-existent file
        non_existent_file = Path("non_existent.gpx")
        gpx_none = self.processor._load_gpx_file(non_existent_file)
        self.assertIsNone(gpx_none)

        # Test with a malformed GPX file
        malformed_file = self.output_dir / "malformed.gpx"
        malformed_file.write_text(
            "<gpx><track><segment><point></point></segment></track>"
        )  # Malformed XML
        gpx_malformed = self.processor._load_gpx_file(malformed_file)
        self.assertIsNone(gpx_malformed)

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

    def test_compress_files(self):
        """
        Test the public compress_files method.
        """
        # Ensure the output directory is clean before compression
        shutil.rmtree(self.output_dir)
        compressed_file_path = self.output_dir / f"compressed_{self.test_gpx_file.name}"
        self.output_dir.mkdir()
        print(f"files to compress: {self.processor._get_input_files()}")
        self.processor.compress_files()

        # Check if the compressed file exists
        self.assertTrue(compressed_file_path.exists())

        # Load the compressed GPX and verify its structure (e.g., fewer points)
        compressed_gpx = gpxpy.parse(open(compressed_file_path, "r", encoding="utf-8"))
        original_gpx = gpxpy.parse(open(self.test_gpx_file, "r", encoding="utf-8"))

        # Assuming kuhkopfsteig.gpx has at least one track/segment
        self.assertGreater(len(original_gpx.tracks), 0)
        self.assertGreater(len(compressed_gpx.tracks), 0)

        original_points_count = sum(len(s.points) for t in original_gpx.tracks for s in t.segments)
        compressed_points_count = sum(
            len(s.points) for t in compressed_gpx.tracks for s in t.segments
        )

        self.assertLess(compressed_points_count, original_points_count)
        # Placeholder: Expect significantly fewer points, e.g., less than 50%
        self.assertLess(compressed_points_count, original_points_count * 0.5)
        # Check that metadata is cleaned
        self.assertIsNone(compressed_gpx.time)
        self.assertFalse(bool(compressed_gpx.extensions))

    def test_merge_files(self):
        """
        Test the public merge_files method.
        """
        # Create a second dummy GPX file for merging
        dummy_gpx_path = self.output_dir / "dummy_merge.gpx"
        dummy_gpx = gpxpy.gpx.GPX()
        dummy_track = gpxpy.gpx.GPXTrack()
        dummy_segment = gpxpy.gpx.GPXTrackSegment()
        dummy_segment.points.append(GPXTrackPoint(latitude=51.0, longitude=14.0, elevation=100))
        dummy_segment.points.append(
            GPXTrackPoint(latitude=51.0001, longitude=14.0001, elevation=101)
        )
        dummy_track.segments.append(dummy_segment)
        dummy_gpx.tracks.append(dummy_track)
        with open(dummy_gpx_path, "w", encoding="utf-8") as f:
            f.write(dummy_gpx.to_xml())

        # Update processor to handle multiple files (directory containing both)
        merge_input_dir = self.output_dir / "merge_input"
        merge_input_dir.mkdir()
        shutil.copy(self.test_gpx_file, merge_input_dir)
        shutil.copy(dummy_gpx_path, merge_input_dir)

        self.processor = BaseGPXProcessor(
            input_=str(merge_input_dir), output=str(self.output_dir), logger=self.logger
        )

        self.processor.merge_files()

        merged_file_path = self.output_dir / "merged_tracks.gpx"
        self.assertTrue(merged_file_path.exists())

        merged_gpx = gpxpy.parse(open(merged_file_path, "r", encoding="utf-8"))

        # Kuhkopfsteig has 1 track, dummy has 1 track. So merged should have 2 tracks.
        self.assertEqual(len(merged_gpx.tracks), 2)  # Placeholder: Expect 2 tracks after merging

        # Verify names
        track_names = [t.name for t in merged_gpx.tracks]
        self.assertTrue(any("kuhkopfsteig" in name for name in track_names))
        self.assertTrue(any("dummy_merge" in name for name in track_names))

        # Check total points - should be reduced
        total_merged_points = sum(len(s.points) for t in merged_gpx.tracks for s in t.segments)
        # Original kuhkopfsteig points
        original_kuhkopf_gpx = gpxpy.parse(open(self.test_gpx_file, "r", encoding="utf-8"))
        original_kuhkopf_points = sum(
            len(s.points) for t in original_kuhkopf_gpx.tracks for s in t.segments
        )
        # Dummy points
        original_dummy_points = sum(len(s.points) for t in dummy_gpx.tracks for s in t.segments)

        # Due to optimization, merged points should be less than sum of original points
        self.assertLess(total_merged_points, original_kuhkopf_points + original_dummy_points)
        self.assertGreater(total_merged_points, 0)  # Must have some points

    def test_extract_pois(self):
        """
        Test the public extract_pois method.
        """
        self.processor.extract_pois()

        poi_file_path = self.output_dir / "extracted_pois.gpx"
        self.assertTrue(poi_file_path.exists())

        poi_gpx = gpxpy.parse(open(poi_file_path, "r", encoding="utf-8"))

        # Kuhkopfsteig has 1 track and 0 routes by default. So it should extract 1 POI.
        # If it had routes with points, it would extract more.
        self.assertEqual(len(poi_gpx.waypoints), 1)  # Placeholder: Expect 1 waypoint (track start)

        # Check some properties of the extracted POI
        if poi_gpx.waypoints:
            poi = poi_gpx.waypoints[0]
            self.assertTrue(poi.name.startswith("POI_"))
            self.assertIn("Start of", poi.description)
            self.assertEqual(poi.type, "Track Start")
            self.assertIsInstance(poi.latitude, float)
            self.assertIsInstance(poi.longitude, float)
            self.assertIsInstance(poi.elevation, float)


if __name__ == "__main__":
    unittest.main()
