"""GPX point simplification and metadata normalization."""

import logging
import math
from collections.abc import Callable
from copy import deepcopy

from gpxpy.gpx import GPXTrackPoint, GPXWaypoint
from pyproj import CRS, Transformer


class TrackPointOptimizer:
    """Optimize track points while keeping source GPX objects unchanged."""

    def __init__(
        self,
        tolerance: float,
        elevation_for: Callable[[GPXTrackPoint | GPXWaypoint], float | None],
        logger: logging.Logger,
    ):
        self.tolerance = tolerance
        self.elevation_for = elevation_for
        self.logger = logger

    @staticmethod
    def calculate_distance(point1: GPXTrackPoint, point2: GPXTrackPoint) -> float:
        """Calculate great-circle distance in meters using the Haversine formula."""
        try:
            lat1, lon1 = math.radians(point1.latitude), math.radians(point1.longitude)
            lat2, lon2 = math.radians(point2.latitude), math.radians(point2.longitude)
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            return 6_371_000 * 2 * math.asin(math.sqrt(a))
        except (AttributeError, TypeError, ValueError):
            return 0.0

    def optimize_track_points(
        self,
        track_points: list[GPXTrackPoint] | list[GPXWaypoint],
        preserve_descriptions: bool = False,
    ) -> list[GPXTrackPoint]:
        """Simplify a track and remove metadata not retained in output."""
        if not track_points:
            return track_points

        try:
            optimized_points = self.douglas_peucker(
                track_points, preserve_descriptions=preserve_descriptions
            )
            for point in optimized_points:
                try:
                    point.time = None
                    if point.latitude is not None:
                        point.latitude = round(point.latitude, 5)
                    if point.longitude is not None:
                        point.longitude = round(point.longitude, 5)
                    point.elevation = self.elevation_for(point)
                    point.extensions = None
                    if hasattr(point, "symbol"):
                        point.symbol = None
                    if hasattr(point, "type"):
                        point.type = None
                    point.comment = None
                    if not preserve_descriptions:
                        point.description = None
                    point.source = None
                    point.link = None
                    point.link_text = None
                    point.link_type = None
                    point.horizontal_dilution = None
                    point.vertical_dilution = None
                    point.position_dilution = None
                    point.age_of_dgps_data = None
                    point.dgps_id = None
                except (AttributeError, TypeError, ValueError) as error:
                    self.logger.warning(f"Error optimizing point: {error}")
            return optimized_points
        except Exception:
            self.logger.exception("Error optimizing track points")
            raise

    def douglas_peucker(
        self,
        track_points: list[GPXTrackPoint] | list[GPXWaypoint],
        preserve_descriptions: bool = False,
    ) -> list[GPXTrackPoint]:
        """Return copied points simplified using a local meter-based projection."""
        if len(track_points) <= 2 or self.tolerance == 0:
            return [deepcopy(point) for point in track_points]

        origin = track_points[0]
        local_crs = CRS.from_proj4(
            f"+proj=aeqd +lat_0={origin.latitude} +lon_0={origin.longitude} "
            "+datum=WGS84 +units=m +no_defs"
        )
        project = Transformer.from_crs("EPSG:4326", local_crs, always_xy=True).transform
        projected = [project(point.longitude, point.latitude) for point in track_points]
        anchors = sorted(
            {
                0,
                len(track_points) - 1,
                *(
                    index
                    for index, point in enumerate(track_points)
                    if preserve_descriptions and point.description is not None
                ),
            }
        )
        keep = [index in anchors for index in range(len(track_points))]
        intervals = list(zip(anchors, anchors[1:]))

        while intervals:
            start, end = intervals.pop()
            x1, y1 = projected[start]
            x2, y2 = projected[end]
            dx, dy = x2 - x1, y2 - y1
            denominator = dx * dx + dy * dy
            max_distance = self.tolerance
            max_index = None

            for index in range(start + 1, end):
                x, y = projected[index]
                if denominator == 0:
                    distance = math.hypot(x - x1, y - y1)
                else:
                    fraction = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / denominator))
                    distance = math.hypot(x - (x1 + fraction * dx), y - (y1 + fraction * dy))
                if distance > max_distance:
                    max_distance = distance
                    max_index = index

            if max_index is not None:
                keep[max_index] = True
                intervals.extend(((start, max_index), (max_index, end)))

        return [deepcopy(point) for point, should_keep in zip(track_points, keep) if should_keep]

    def optimize_waypoint(
        self, waypoint: GPXWaypoint, preserve_descriptions: bool = False
    ) -> GPXWaypoint:
        """Normalize a copied waypoint."""
        waypoint = deepcopy(waypoint)
        try:
            if waypoint.latitude is not None:
                waypoint.latitude = round(waypoint.latitude, 5)
            if waypoint.longitude is not None:
                waypoint.longitude = round(waypoint.longitude, 5)
            waypoint.elevation = self.elevation_for(waypoint)
            waypoint.time = None
            waypoint.extensions = None
            if hasattr(waypoint, "symbol"):
                waypoint.symbol = None
            if hasattr(waypoint, "type"):
                waypoint.type = None
            waypoint.comment = None
            if not preserve_descriptions:
                waypoint.description = None
            waypoint.source = None
            waypoint.link = None
            waypoint.link_text = None
            waypoint.link_type = None
        except (AttributeError, TypeError, ValueError) as error:
            self.logger.warning(f"Error optimizing waypoint: {error}")
        return waypoint
