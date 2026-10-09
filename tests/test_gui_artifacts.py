import logging
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import gpxpy
from gpxpy.gpx import (
    GPX,
    GPXRoute,
    GPXTrack,
    GPXTrackPoint,
    GPXTrackSegment,
    GPXWaypoint,
)
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from gpx_kml_converter.core.gpx_plotter import GPXPlotter
from gpx_kml_converter.gui.artifacts import (
    ArtifactIdentity,
    artifact_groups,
    artifact_label,
    artifact_metadata,
    plot_reference,
    resolve_artifact,
    selected_input_paths,
    summarize_gpx,
)


class TestGuiArtifacts(unittest.TestCase):
    def setUp(self):
        self.gpx = GPX()
        self.gpx.creator = "test"
        self.gpx.name = "Sample"
        self.gpx.description = "Workspace source"

        first_track = GPXTrack(name="Loop", description="First track")
        first_segment = GPXTrackSegment()
        first_segment.points.extend(
            [
                GPXTrackPoint(latitude=50.0, longitude=10.0, elevation=100),
                GPXTrackPoint(latitude=50.001, longitude=10.002, elevation=120),
            ]
        )
        first_track.segments.append(first_segment)

        duplicate_track = GPXTrack(name="Loop", description="Second track")
        second_segment = GPXTrackSegment()
        second_segment.points.extend(
            [
                GPXTrackPoint(latitude=51.0, longitude=11.0, elevation=200),
                GPXTrackPoint(latitude=51.002, longitude=11.001, elevation=215),
            ]
        )
        duplicate_track.segments.append(second_segment)

        route = GPXRoute(name="Ridge", description="Route description")
        route.points.extend(
            [
                GPXTrackPoint(latitude=52.0, longitude=12.0),
                GPXTrackPoint(latitude=52.001, longitude=12.001),
            ]
        )

        self.gpx.tracks.extend((first_track, duplicate_track))
        self.gpx.routes.append(route)
        self.gpx.waypoints.append(
            GPXWaypoint(
                latitude=53.0,
                longitude=13.0,
                elevation=321,
                name="Summit",
                description="Waypoint description",
                symbol="Flag",
            )
        )

    def test_file_summary_counts_artifacts_and_sums_track_distance(self):
        summary = summarize_gpx(self.gpx)

        self.assertEqual(
            (summary.track_count, summary.route_count, summary.waypoint_count), (2, 1, 1)
        )
        self.assertEqual(summary.artifact_count, 4)
        expected_distance = sum(track.length_2d() for track in self.gpx.tracks)
        self.assertAlmostEqual(summary.total_track_distance_m, expected_distance)
        file_identity = ArtifactIdentity("input", Path("sample.gpx"), "file")
        metadata = dict(artifact_metadata(self.gpx, file_identity, summary))
        self.assertEqual(metadata["Total track distance"], f"{expected_distance / 1000:.2f} km")
        self.assertEqual(metadata["POIs"], "1")

    def test_duplicate_names_resolve_by_artifact_identity_not_label(self):
        first = ArtifactIdentity("input", Path("sample.gpx"), "track", 0)
        second = ArtifactIdentity("input", Path("sample.gpx"), "track", 1)

        self.assertIs(resolve_artifact(self.gpx, first), self.gpx.tracks[0])
        self.assertIs(resolve_artifact(self.gpx, second), self.gpx.tracks[1])
        self.assertNotEqual(artifact_label(self.gpx, first), artifact_label(self.gpx, second))
        self.assertEqual(dict(artifact_metadata(self.gpx, first))["Description"], "First track")
        self.assertEqual(dict(artifact_metadata(self.gpx, second))["Description"], "Second track")
        self.assertEqual(plot_reference(first), ("track", 0))
        self.assertEqual(plot_reference(second), ("track", 1))

    def test_artifact_browser_groups_keep_collection_file_and_index_identity(self):
        groups = artifact_groups(self.gpx, "output", Path("result.gpx"))

        self.assertEqual([label for label, _identities in groups], ["Tracks", "Routes", "POIs"])
        self.assertEqual(
            [
                (identity.collection, identity.file_path, identity.kind, identity.index)
                for _label, identities in groups
                for identity in identities
            ],
            [
                ("output", Path("result.gpx"), "track", 0),
                ("output", Path("result.gpx"), "track", 1),
                ("output", Path("result.gpx"), "route", 0),
                ("output", Path("result.gpx"), "waypoint", 0),
            ],
        )

    def test_artifact_browser_omits_empty_groups(self):
        self.assertEqual(artifact_groups(GPX(), "input", Path("empty.gpx")), ())

    def test_route_and_waypoint_metadata_and_plot_targets_use_indexes(self):
        route = ArtifactIdentity("output", Path("result.gpx"), "route", 0)
        waypoint = ArtifactIdentity("output", Path("result.gpx"), "waypoint", 0)

        self.assertEqual(dict(artifact_metadata(self.gpx, route))["Distance"][-2:], "km")
        self.assertEqual(dict(artifact_metadata(self.gpx, waypoint))["Symbol"], "Flag")
        self.assertEqual(plot_reference(route), ("route", 0))
        self.assertEqual(plot_reference(waypoint), ("waypoint", 0))
        self.assertIsNone(plot_reference(ArtifactIdentity("input", Path("sample.gpx"), "file")))

    def test_map_and_profile_plot_the_indexed_duplicate_name_track(self):
        figure = Figure()
        canvas = FigureCanvasAgg(figure)
        plotter = GPXPlotter.__new__(GPXPlotter)
        plotter.fig = figure
        plotter.ax = figure.add_subplot(111)
        plotter.canvas = canvas
        plotter.logger = logging.getLogger(__name__)
        plotter.country_borders_gdf = None

        plotter.plot_gpx_map(self.gpx, ("track", 1))
        self.assertEqual(
            [line.get_color() for line in plotter.ax.lines[:2]], ["darkblue", "darkorange"]
        )

        plotter.plot_track_profile(self.gpx, 1)
        self.assertEqual(list(plotter.ax.lines[0].get_ydata()), [200, 215])
        self.assertIn("Loop", plotter.ax.get_title())

    def test_empty_file_metadata_explains_no_artifacts(self):
        metadata = dict(
            artifact_metadata(GPX(), ArtifactIdentity("input", Path("empty.gpx"), "file"))
        )

        self.assertEqual(metadata["Artifacts"], "No tracks, routes, or POIs")
        self.assertEqual(metadata["Total track distance"], "0.00 km")

    def test_batch_selection_uses_input_file_nodes_and_empty_means_all(self):
        first = Path("first.gpx")
        second = Path("second.gpx")
        third = Path("third.gpx")
        identities = [
            ArtifactIdentity("input", first, "file"),
            ArtifactIdentity("input", second, "track", 0),
            ArtifactIdentity("input", third, "file"),
            ArtifactIdentity("output", second, "file"),
        ]

        self.assertEqual(selected_input_paths([first, second, third], identities), [first, third])
        self.assertEqual(selected_input_paths([first, second, third], []), [first, second, third])
        self.assertEqual(
            selected_input_paths(
                [first, second, third], [ArtifactIdentity("output", second, "file")]
            ),
            [first, second, third],
        )

    def test_fixture_and_serialized_gpx_are_parsed_before_aggregation(self):
        fixture = Path(__file__).parent.parent / "examples" / "kuhkopfsteig.gpx"
        with fixture.open(encoding="utf-8") as source:
            fixture_gpx = gpxpy.parse(source)
        self.assertEqual(summarize_gpx(fixture_gpx).track_count, len(fixture_gpx.tracks))

        with TemporaryDirectory() as temp_dir:
            saved_path = Path(temp_dir) / "sample.gpx"
            saved_path.write_text(self.gpx.to_xml(), encoding="utf-8")
            with saved_path.open(encoding="utf-8") as saved_file:
                restored = gpxpy.parse(saved_file)

        restored_summary = summarize_gpx(restored)
        self.assertEqual(
            (
                restored_summary.track_count,
                restored_summary.route_count,
                restored_summary.waypoint_count,
            ),
            (2, 1, 1),
        )
        restored_identity = ArtifactIdentity("input", saved_path, "track", 1)
        self.assertEqual(
            dict(artifact_metadata(restored, restored_identity))["Description"], "Second track"
        )


if __name__ == "__main__":
    unittest.main()
