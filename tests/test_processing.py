import logging
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

import gpxpy
from gpxpy.gpx import GPX, GPXTrack, GPXTrackPoint, GPXTrackSegment, GPXWaypoint

from gpx_kml_converter.application.processing import process_gpx_files
from gpx_kml_converter.core.file_loader import FileOrigin, GeoFileManager


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

    def test_default_compress_output_uses_source_basename_and_keeps_source_unchanged(self):
        source_path = Path(self.temp_dir.name) / "ride.gpx"
        source = GPX()
        track = GPXTrack(name="Ride")
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
        source_path.write_text(source.to_xml(), encoding="utf-8")
        original_contents = source_path.read_bytes()
        loaded = GeoFileManager(self.logger).load_files_with_origins([source_path])

        outputs = process_gpx_files(
            [next(iter(loaded.values())).gpx],
            mode="compress",
            output=None,
            tolerance=10,
            date_format="%Y-%m-%d",
            elevation=False,
            logger=self.logger,
            source_origins=[next(iter(loaded.values())).origin],
        )

        output_path = next(iter(outputs))
        self.assertEqual(output_path.parent, source_path.parent)
        self.assertRegex(output_path.name, r"^ride_processed_\d{4}-\d{2}-\d{2}_\d{6}\.gpx$")
        self.assertEqual(source_path.read_bytes(), original_contents)
        saved_gpx = gpxpy.parse(output_path.read_text(encoding="utf-8"))
        self.assertEqual(saved_gpx.tracks[0].name, "Ride")

    def test_zip_processing_uses_archive_folder_and_member_basename(self):
        source_path = Path(__file__).parent.parent / "examples" / "kuhkopfsteig.gpx"
        archive_path = Path(self.temp_dir.name) / "trip.zip"
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.write(source_path, "routes/ride.gpx")
        original_contents = archive_path.read_bytes()
        loaded = GeoFileManager(self.logger).load_files_with_origins([archive_path])
        loaded_file = next(iter(loaded.values()))

        outputs = process_gpx_files(
            [loaded_file.gpx],
            mode="compress",
            output=None,
            tolerance=10,
            date_format="%Y-%m-%d",
            elevation=False,
            logger=self.logger,
            source_origins=[loaded_file.origin],
        )

        output_path = next(iter(outputs))
        self.assertEqual(output_path.parent, Path(self.temp_dir.name) / "trip")
        self.assertRegex(output_path.name, r"^ride_processed_\d{4}-\d{2}-\d{2}_\d{6}\.gpx$")
        self.assertEqual(archive_path.read_bytes(), original_contents)
        self.assertTrue(gpxpy.parse(output_path.read_text(encoding="utf-8")).tracks)

    def test_default_merge_writes_flat_timestamped_filename(self):
        first = GPX()
        first.waypoints.append(GPXWaypoint(latitude=48.0, longitude=11.0, name="Start"))

        original_directory = Path.cwd()
        try:
            os.chdir(self.temp_dir.name)
            outputs = process_gpx_files(
                [first],
                mode="merge",
                output=None,
                tolerance=10,
                date_format="%Y-%m-%d",
                elevation=False,
                logger=self.logger,
            )
        finally:
            os.chdir(original_directory)

        output_path = next(iter(outputs))
        self.assertEqual(output_path.parent.resolve(), Path(self.temp_dir.name).resolve())
        self.assertRegex(output_path.name, r"^gpx_processed_\d{4}-\d{2}-\d{2}_\d{6}\.gpx$")
        self.assertEqual(
            gpxpy.parse(output_path.read_text(encoding="utf-8")).waypoints[0].name, "Start"
        )

    def test_duplicate_source_names_in_one_batch_get_distinct_outputs(self):
        first = GPX()
        second = GPX()
        origins = [
            FileOrigin(Path(self.temp_dir.name) / "same.gpx"),
            FileOrigin(Path(self.temp_dir.name) / "same.kml"),
        ]

        outputs = process_gpx_files(
            [first, second],
            mode="compress",
            output=None,
            tolerance=10,
            date_format="%Y-%m-%d",
            elevation=False,
            logger=self.logger,
            source_origins=origins,
        )

        self.assertEqual(len(outputs), 2)
        names = [path.name for path in outputs]
        self.assertRegex(names[0], r"^same_processed_\d{4}-\d{2}-\d{2}_\d{6}\.gpx$")
        self.assertRegex(names[1], r"^same_processed_\d{4}-\d{2}-\d{2}_\d{6}_2\.gpx$")
        for path in outputs:
            self.assertIsInstance(gpxpy.parse(path.read_text(encoding="utf-8")), GPX)

    def test_generated_gpx_can_be_reused_in_a_second_processing_stage(self):
        source = GPX()
        track = GPXTrack(name="Reusable Track")
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

        first_stage = process_gpx_files(
            [source],
            mode="compress",
            output=self.output_dir / "first-stage",
            tolerance=10,
            date_format="%Y-%m-%d",
            elevation=False,
            logger=self.logger,
        )
        first_stage_path, first_stage_gpx = next(iter(first_stage.items()))

        second_stage = process_gpx_files(
            [first_stage_gpx],
            mode="compress",
            output=self.output_dir / "second-stage",
            tolerance=10,
            date_format="%Y-%m-%d",
            elevation=False,
            logger=self.logger,
        )

        self.assertTrue(first_stage_path.is_file())
        second_stage_path = next(iter(second_stage))
        saved_gpx = gpxpy.parse(second_stage_path.read_text(encoding="utf-8"))
        self.assertEqual(saved_gpx.tracks[0].name, "Reusable Track")
        self.assertEqual(len(saved_gpx.tracks[0].segments[0].points), 2)

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
