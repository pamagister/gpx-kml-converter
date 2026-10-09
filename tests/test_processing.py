import logging
import tempfile
import unittest
from pathlib import Path

import gpxpy
from gpxpy.gpx import GPX, GPXTrack, GPXTrackPoint, GPXTrackSegment, GPXWaypoint

from gpx_kml_converter.application.processing import process_gpx_files


class UnavailableElevationProvider:
    def get_elevation(self, latitude, longitude):
        return None


class TestProcessingService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name) / "output"
        self.logger = logging.getLogger("test.processing")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_compress_writes_round_trippable_simplified_gpx(self):
        source = GPX()
        source.name = "Test Track"
        track = GPXTrack(name="Coast")
        segment = GPXTrackSegment()
        segment.points.extend(
            [
                GPXTrackPoint(latitude=50.0, longitude=10.0),
                GPXTrackPoint(latitude=50.00001, longitude=10.0005),
                GPXTrackPoint(latitude=50.0, longitude=10.001),
            ]
        )
        track.segments.append(segment)
        source.tracks.append(track)

        outputs = process_gpx_files(
            [source],
            mode="compress",
            output=self.output_dir,
            tolerance=10,
            date_format="%Y-%m-%d",
            elevation=False,
            logger=self.logger,
        )

        self.assertEqual(len(outputs), 1)
        output_path = next(iter(outputs))
        self.assertTrue(output_path.is_file())
        saved_gpx = gpxpy.parse(output_path.read_text(encoding="utf-8"))
        saved_points = saved_gpx.tracks[0].segments[0].points
        self.assertEqual(len(saved_points), 2)
        self.assertEqual(saved_points[0].latitude, 50.0)
        self.assertEqual(saved_points[-1].longitude, 10.001)
        self.assertEqual(len(source.tracks[0].segments[0].points), 3)

    def test_merge_preserves_waypoints_in_saved_gpx(self):
        first = GPX()
        first.waypoints.append(
            GPXWaypoint(latitude=48.0, longitude=11.0, name="Start", description="First")
        )
        second = GPX()
        second.waypoints.append(
            GPXWaypoint(latitude=49.0, longitude=12.0, name="Finish", description="Last")
        )

        outputs = process_gpx_files(
            [first, second],
            mode="merge",
            output=self.output_dir,
            tolerance=10,
            date_format="%Y-%m-%d",
            elevation=False,
            logger=self.logger,
        )

        output_path = next(iter(outputs))
        saved_gpx = gpxpy.parse(output_path.read_text(encoding="utf-8"))
        self.assertEqual(
            [(point.name, point.description) for point in saved_gpx.waypoints],
            [("Start", "First"), ("Finish", "Last")],
        )

    def test_extract_pois_writes_track_start(self):
        source = GPX()
        track = GPXTrack(name="Morning walk")
        segment = GPXTrackSegment()
        segment.points.append(GPXTrackPoint(latitude=47.0, longitude=8.0, elevation=420))
        track.segments.append(segment)
        source.tracks.append(track)

        outputs = process_gpx_files(
            [source],
            mode="extract-pois",
            output=self.output_dir,
            tolerance=10,
            date_format="%Y-%m-%d",
            elevation=False,
            logger=self.logger,
        )

        saved_gpx = gpxpy.parse(next(iter(outputs)).read_text(encoding="utf-8"))
        self.assertEqual(len(saved_gpx.waypoints), 1)
        self.assertEqual(saved_gpx.waypoints[0].name, "Track_Start_POI_001")
        self.assertEqual(saved_gpx.waypoints[0].latitude, 47.0)
        self.assertIsNone(saved_gpx.waypoints[0].elevation)

    def test_offline_elevation_fallback_survives_processing_round_trip(self):
        source = GPX()
        track = GPXTrack(name="Known elevation")
        segment = GPXTrackSegment()
        segment.points.append(GPXTrackPoint(latitude=47.0, longitude=8.0, elevation=423.26))
        track.segments.append(segment)
        source.tracks.append(track)

        outputs = process_gpx_files(
            [source],
            mode="compress",
            output=self.output_dir,
            tolerance=10,
            date_format="%Y-%m-%d",
            elevation=True,
            logger=self.logger,
            elevation_provider=UnavailableElevationProvider(),
        )

        saved_gpx = gpxpy.parse(next(iter(outputs)).read_text(encoding="utf-8"))
        self.assertEqual(saved_gpx.tracks[0].segments[0].points[0].elevation, 423.3)

    def test_unknown_mode_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported processing mode"):
            process_gpx_files(
                [],
                mode="unknown",
                output=self.output_dir,
                tolerance=10,
                date_format="%Y-%m-%d",
                elevation=False,
                logger=self.logger,
            )


if __name__ == "__main__":
    unittest.main()
