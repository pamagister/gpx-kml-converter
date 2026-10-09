"""High-level GPX processing workflows."""

import logging
import math
import os
import traceback
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

import gpxpy
from gpxpy.gpx import GPX, GPXTrackPoint, GPXWaypoint

from gpx_kml_converter.core.elevation import (
    ElevationProvider,
    ElevationService,
    SRTMElevationProvider,
)
from gpx_kml_converter.core.file_loader import FileOrigin, GeoFileManager
from gpx_kml_converter.core.geometry import TrackPointOptimizer
from gpx_kml_converter.core.gpx_serializer import GPXSerializer

NAME = "gpx_kml_converter"


class BaseGPXProcessor:
    def __init__(
        self,
        input_: list[GPX] | str | Path,
        output: str | Path | None = None,
        tolerance: float = 10.0,
        date_format: str = "%Y-%m-%d",
        elevation: bool = True,
        logger: logging.Logger | None = None,
        elevation_provider: ElevationProvider | None = None,
        source_origins: Sequence[FileOrigin] | None = None,
    ):
        self.logger = logger if logger is not None else logging.getLogger(__name__)
        if isinstance(input_, str) or isinstance(input_, Path):
            loaded_files = GeoFileManager(logger=self.logger).load_files_with_origins(
                [Path(input_)]
            )
            self.input = [loaded.gpx for loaded in loaded_files.values()]
            self.source_origins = [loaded.origin for loaded in loaded_files.values()]
        elif isinstance(input_, list) and all(isinstance(g, GPX) for g in input_):
            self.input = input_
            if source_origins is not None and len(source_origins) != len(self.input):
                raise ValueError("source_origins must have one entry per input GPX object.")
            self.source_origins = list(source_origins) if source_origins is not None else []
        else:
            raise ValueError("input_gpx_list must be a list of gpxpy.gpx.GPX objects.")

        self.output = output
        if not math.isfinite(tolerance) or tolerance < 0:
            raise ValueError("tolerance must be a finite, non-negative number of meters.")
        self.tolerance = tolerance
        self.date_format = date_format
        self.include_elevation = elevation
        if elevation and elevation_provider is None:
            elevation_provider = SRTMElevationProvider(self.logger)
        self._elevation_service = ElevationService(elevation_provider, enabled=elevation)
        self._optimizer = TrackPointOptimizer(
            tolerance=tolerance,
            elevation_for=self._get_adjusted_elevation,
            logger=self.logger,
        )
        self._serializer = GPXSerializer(self.logger)

    def _get_output_folder(self) -> Path:
        """Get the output folder path, create if not exists."""
        if self.output and self.output != "auto":
            output_path = Path(self.output)
        else:
            timestamp = datetime.now().strftime(
                f"{self.date_format}_%H%M%S"
            )  # Added seconds for uniqueness
            output_path = Path.cwd() / f"gpx_processed_{timestamp}"

        output_path.mkdir(parents=True, exist_ok=True)
        return output_path

    def _timestamp(self) -> str:
        return datetime.now().strftime(f"{self.date_format}_%H%M%S")

    @staticmethod
    def _unique_batch_path(output_path: Path, used_paths: set[str]) -> Path:
        """Avoid two inputs in one batch overwriting the same generated path."""
        candidate = output_path
        suffix = 2
        while os.path.normcase(str(candidate.absolute())) in used_paths:
            candidate = output_path.with_name(f"{output_path.stem}_{suffix}{output_path.suffix}")
            suffix += 1
        used_paths.add(os.path.normcase(str(candidate.absolute())))
        return candidate

    def _get_adjusted_elevation(self, point: GPXTrackPoint | GPXWaypoint) -> float | None:
        """Get provider elevation, falling back to the source value or 0."""
        return self._elevation_service.get_adjusted_elevation(point)

    @staticmethod
    def _calculate_distance(point1: GPXTrackPoint, point2: GPXTrackPoint) -> float:
        """Calculate distance between two GPX points in meters."""
        return TrackPointOptimizer.calculate_distance(point1, point2)

    def _optimize_track_points(
        self,
        track_points: list[GPXTrackPoint] | list[GPXWaypoint],
        preserve_descriptions: bool = False,
    ) -> list[GPXTrackPoint]:
        """Delegate point cleanup and simplification to the geometry component."""
        self._optimizer.tolerance = self.tolerance
        return self._optimizer.optimize_track_points(
            track_points, preserve_descriptions=preserve_descriptions
        )

    def _douglas_peucker(
        self,
        track_points: list[GPXTrackPoint] | list[GPXWaypoint],
        preserve_descriptions: bool = False,
    ) -> list[GPXTrackPoint]:
        """Return copied points simplified using a local meter-based projection."""
        self._optimizer.tolerance = self.tolerance
        return self._optimizer.douglas_peucker(
            track_points, preserve_descriptions=preserve_descriptions
        )

    def _optimize_waypoint(
        self, waypoint: GPXWaypoint, preserve_descriptions: bool = False
    ) -> GPXWaypoint:
        """Delegate waypoint cleanup to the geometry component."""
        return self._optimizer.optimize_waypoint(
            waypoint, preserve_descriptions=preserve_descriptions
        )

    def _save_gpx_file(
        self, gpx: GPX, output_path: Path, original_file_path: Path | None = None
    ) -> Path | None:
        """Save GPX through the serialization component."""
        return self._serializer.save(gpx, output_path, original_file_path)

    def compress_files(self) -> dict[Path, GPX]:
        """Shrink the size of all given gpx/kml files by optimizing track points."""
        generated_gpx_map = {}
        explicit_output = self.output is not None and str(self.output) != "auto"
        timestamp = self._timestamp()
        self.logger.info(f"Processing {len(self.input)} GPX objects for compression...")
        used_paths: set[str] = set()

        for idx, gpx_obj in enumerate(self.input):
            try:
                optimized_gpx = gpxpy.gpx.GPX()
                optimized_gpx.creator = gpx_obj.creator
                optimized_gpx.name = f"Optimized_{gpx_obj.name or f'Track_{idx + 1}'}"

                # Process tracks
                for track in gpx_obj.tracks:
                    new_track = self._optimize_track(track)
                    if new_track.segments:
                        optimized_gpx.tracks.append(new_track)

                # Process routes
                for route in gpx_obj.routes:
                    new_route = gpxpy.gpx.GPXRoute()
                    new_route.name = route.name
                    optimized_points = self._optimize_track_points(route.points)
                    if optimized_points:
                        new_route.points.extend(optimized_points)
                        optimized_gpx.routes.append(new_route)

                # Process waypoints (just add them, they are typically not "optimized" by distance)
                for waypoint in gpx_obj.waypoints:
                    optimized_gpx.waypoints.append(self._optimize_waypoint(waypoint))

                # Save the optimized GPX
                origin = self.source_origins[idx] if idx < len(self.source_origins) else None
                if explicit_output:
                    output_folder = Path(self.output)
                elif origin is not None:
                    output_folder = origin.output_directory
                else:
                    output_folder = Path.cwd()
                output_folder.mkdir(parents=True, exist_ok=True)
                source_stem = (
                    origin.output_stem if origin is not None else gpx_obj.name or f"file_{idx + 1}"
                )
                output_path = self._unique_batch_path(
                    output_folder / f"{source_stem}_processed_{timestamp}.gpx", used_paths
                )
                saved_path = self._save_gpx_file(
                    optimized_gpx,
                    output_path,
                    origin.source_path if origin is not None else None,
                )
                if saved_path:
                    generated_gpx_map[saved_path] = optimized_gpx
                    self.logger.info(
                        f"Compressed and saved {gpx_obj.name or f'file_{idx + 1}'} "
                        f"to {output_path.name}"
                    )

            except Exception as e:
                self.logger.error(
                    f"Error compressing GPX object {gpx_obj.name or f'file_{idx + 1}'}: {e}"
                )
                self.logger.debug(f"Full traceback:\n{traceback.format_exc()}")
                continue
        return generated_gpx_map

    def _optimize_track(self, track, preserve_descriptions: bool = False):
        new_track = gpxpy.gpx.GPXTrack()
        new_track.name = track.name
        if preserve_descriptions:
            new_track.description = track.description
        for segment in track.segments:
            optimized_points = self._optimize_track_points(
                segment.points, preserve_descriptions=preserve_descriptions
            )
            if optimized_points:
                new_segment = gpxpy.gpx.GPXTrackSegment()
                new_segment.points.extend(optimized_points)
                new_track.segments.append(new_segment)
        return new_track

    def merge_files(self) -> dict[Path, GPX]:
        """Merge all given GPX objects into a single GPX file."""
        if not self.input:
            self.logger.warning("No GPX objects provided for merging.")
            return {}

        merged_gpx = gpxpy.gpx.GPX()
        merged_gpx.creator = NAME
        merged_gpx.name = "Merged GPX"

        total_tracks = 0
        total_routes = 0
        total_waypoints = 0

        for idx, gpx_obj in enumerate(self.input):
            try:
                # Merge tracks
                # Process tracks
                for track in gpx_obj.tracks:
                    new_track = self._optimize_track(track, preserve_descriptions=True)
                    if new_track.segments:
                        merged_gpx.tracks.append(new_track)
                        total_tracks += 1

                # Process routes
                for route in gpx_obj.routes:
                    new_route = gpxpy.gpx.GPXRoute()
                    new_route.name = route.name
                    new_route.description = route.description
                    optimized_points = self._optimize_track_points(
                        route.points, preserve_descriptions=True
                    )
                    if optimized_points:
                        new_route.points.extend(optimized_points)
                        merged_gpx.routes.append(new_route)
                        total_routes += 1

                # Merge waypoints
                for waypoint in gpx_obj.waypoints:
                    merged_gpx.waypoints.append(
                        self._optimize_waypoint(waypoint, preserve_descriptions=True)
                    )
                    total_waypoints += 1
                self.logger.debug(
                    f"Merged contents of GPX object {gpx_obj.name or f'file_{idx + 1}'}"
                )
            except Exception as e:
                self.logger.error(
                    f"Error merging GPX object {gpx_obj.name or f'file_{idx + 1}'}: {e}"
                )
                self.logger.debug(f"Full traceback:\n{traceback.format_exc()}")
                continue

        output_folder = (
            Path(self.output)
            if self.output is not None and str(self.output) != "auto"
            else Path.cwd()
        )
        output_folder.mkdir(parents=True, exist_ok=True)
        output_path = output_folder / f"gpx_processed_{self._timestamp()}.gpx"
        saved_path = self._save_gpx_file(merged_gpx, output_path)

        if saved_path:
            self.logger.info(
                f"Merged {total_tracks} tracks, {total_routes} routes, "
                f"and {total_waypoints} waypoints into {output_path.name}"
            )
            return {saved_path: merged_gpx}
        return {}

    def extract_pois(self) -> dict[Path, GPX]:
        """Extract POIs (Points of Interest) from tracks and routes into a new GPX file."""
        if not self.input:
            self.logger.warning("No GPX objects provided for POI extraction.")
            return {}

        poi_gpx = gpxpy.gpx.GPX()
        poi_gpx.creator = NAME
        poi_gpx.name = "Extracted POIs"
        poi_counter = 1

        for idx, gpx_obj in enumerate(self.input):
            try:
                # Extract POIs from tracks
                for track_idx, track in enumerate(gpx_obj.tracks):
                    if track.segments:
                        # Consider the first point of the first segment as a POI
                        first_point = track.segments[0].points[0]
                        waypoint = gpxpy.gpx.GPXWaypoint(
                            latitude=first_point.latitude,
                            longitude=first_point.longitude,
                            elevation=self._get_adjusted_elevation(first_point),
                            time=first_point.time,
                        )
                        waypoint.name = f"Track_Start_POI_{poi_counter:03d}"
                        waypoint.description = (
                            f"Start of track {track.name or f'Track_{track_idx + 1}'}"
                        )
                        waypoint.type = "Track Start"
                        poi_gpx.waypoints.append(waypoint)
                        poi_counter += 1

                # Extract POIs from routes
                for route_idx, route in enumerate(gpx_obj.routes):
                    if route.points:
                        # Consider the first point of the route as a POI
                        first_point = route.points[0]
                        waypoint = gpxpy.gpx.GPXWaypoint(
                            latitude=first_point.latitude,
                            longitude=first_point.longitude,
                            elevation=self._get_adjusted_elevation(first_point),
                            time=first_point.time,
                        )
                        waypoint.name = f"Route_Start_POI_{poi_counter:03d}"
                        waypoint.description = (
                            f"Start of route {route.name or f'Route_{route_idx + 1}'}"
                        )
                        waypoint.type = "Route Start"
                        poi_gpx.waypoints.append(self._optimize_waypoint(waypoint))
                        poi_counter += 1

                # Add existing waypoints directly
                for waypoint in gpx_obj.waypoints:
                    poi_gpx.waypoints.append(self._optimize_waypoint(waypoint))
                    poi_counter += 1

            except Exception as e:
                self.logger.error(
                    f"Error processing GPX object {gpx_obj.name or f'file_{idx + 1}'} "
                    f"during POI extraction: {e}"
                )
                self.logger.debug(f"Full traceback:\n{traceback.format_exc()}")
                continue

        # Save POI file
        output_folder = self._get_output_folder()
        output_path = output_folder / "extracted_pois.gpx"
        saved_path = self._save_gpx_file(poi_gpx, output_path)

        if saved_path:
            self.logger.info(
                f"POI file saved with {len(poi_gpx.waypoints)} waypoints: {output_path.name}"
            )
            return {saved_path: poi_gpx}
        return {}
