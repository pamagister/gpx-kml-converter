"""Stable identities and metadata helpers for the GUI artifact browser."""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from gpxpy.gpx import GPX, GPXRoute, GPXTrack, GPXWaypoint

FileCollection = Literal["input", "output"]
ArtifactKind = Literal["file", "track", "route", "waypoint"]
PlottedArtifactKind = Literal["track", "route", "waypoint"]


@dataclass(frozen=True)
class ArtifactIdentity:
    collection: FileCollection
    file_path: Path
    kind: ArtifactKind
    index: int | None = None


@dataclass(frozen=True)
class FileSummary:
    track_count: int
    route_count: int
    waypoint_count: int
    total_track_distance_m: float

    @property
    def artifact_count(self) -> int:
        return self.track_count + self.route_count + self.waypoint_count


def summarize_gpx(gpx: GPX) -> FileSummary:
    """Calculate file-level artifact counts and total track distance."""
    return FileSummary(
        track_count=len(gpx.tracks),
        route_count=len(gpx.routes),
        waypoint_count=len(gpx.waypoints),
        total_track_distance_m=sum(track.length_2d() or 0.0 for track in gpx.tracks),
    )


def resolve_artifact(gpx: GPX, identity: ArtifactIdentity) -> GPXTrack | GPXRoute | GPXWaypoint:
    """Resolve an artifact by its collection-independent kind and stable index."""
    index = identity.index
    if index is None or index < 0:
        raise ValueError("Artifact identity must have a non-negative index.")
    artifacts = {
        "track": gpx.tracks,
        "route": gpx.routes,
        "waypoint": gpx.waypoints,
    }.get(identity.kind)
    if artifacts is None:
        raise ValueError(f"Unsupported artifact kind: {identity.kind}")
    try:
        return artifacts[index]
    except IndexError as error:
        raise ValueError(f"{identity.kind.title()} index is out of range.") from error


def artifact_label(gpx: GPX, identity: ArtifactIdentity) -> str:
    """Return readable tree text without using it as an artifact identifier."""
    if identity.kind == "file":
        return identity.file_path.name
    if identity.index is None:
        raise ValueError("Artifact identity must have an index.")
    artifact = resolve_artifact(gpx, identity)
    label_type = {"track": "Track", "route": "Route", "waypoint": "POI"}[identity.kind]
    return f"{label_type} {identity.index + 1}: {artifact.name or '(unnamed)'}"


def plot_reference(identity: ArtifactIdentity) -> tuple[PlottedArtifactKind, int] | None:
    """Return the GPX-local plot target for an artifact identity."""
    if identity.kind == "file":
        return None
    if identity.index is None or identity.index < 0:
        raise ValueError("Artifact identity must have a non-negative index.")
    return identity.kind, identity.index


def selected_input_paths(
    file_paths: Iterable[Path], selected_identities: Iterable[ArtifactIdentity]
) -> list[Path]:
    """Resolve selected input file identities; no selected files means all inputs."""
    selected_paths = {
        identity.file_path
        for identity in selected_identities
        if identity.collection == "input" and identity.kind == "file"
    }
    ordered_paths = list(file_paths)
    return [path for path in ordered_paths if path in selected_paths] or ordered_paths


def artifact_metadata(
    gpx: GPX, identity: ArtifactIdentity, summary: FileSummary | None = None
) -> tuple[tuple[str, str], ...]:
    """Return context metadata for one file or GPX artifact."""
    if identity.kind == "file":
        summary = summary or summarize_gpx(gpx)
        return (
            ("File", identity.file_path.name),
            ("Name", gpx.name or "N/A"),
            ("Creator", gpx.creator or "N/A"),
            ("Description", gpx.description or "N/A"),
            ("Tracks", str(summary.track_count)),
            ("Routes", str(summary.route_count)),
            ("POIs", str(summary.waypoint_count)),
            ("Total track distance", f"{summary.total_track_distance_m / 1000:.2f} km"),
            (
                "Artifacts",
                "No tracks, routes, or POIs"
                if summary.artifact_count == 0
                else str(summary.artifact_count),
            ),
        )

    artifact = resolve_artifact(gpx, identity)
    values = [
        ("Type", identity.kind.title()),
        ("Name", artifact.name or "N/A"),
        ("Description", artifact.description or "N/A"),
    ]
    if isinstance(artifact, GPXTrack):
        point_count = sum(len(segment.points) for segment in artifact.segments)
        values.extend(
            (
                ("Segments", str(len(artifact.segments))),
                ("Points", str(point_count)),
                ("Distance", f"{(artifact.length_2d() or 0.0) / 1000:.2f} km"),
            )
        )
    elif isinstance(artifact, GPXRoute):
        values.extend(
            (
                ("Points", str(len(artifact.points))),
                ("Distance", f"{(artifact.length() or 0.0) / 1000:.2f} km"),
            )
        )
    elif isinstance(artifact, GPXWaypoint):
        values.extend(
            (
                ("Latitude", str(artifact.latitude)),
                ("Longitude", str(artifact.longitude)),
                (
                    "Elevation",
                    f"{artifact.elevation:g} m" if artifact.elevation is not None else "N/A",
                ),
                ("Symbol", artifact.symbol or "N/A"),
            )
        )
    return tuple(values)
