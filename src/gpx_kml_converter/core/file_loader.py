"""Loading GPX and KML data, including supported files inside ZIP archives."""

import logging
import traceback
import zipfile
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import gpxpy
from gpxpy.gpx import GPX, GPXXMLSyntaxException


@dataclass(frozen=True)
class FileOrigin:
    """Physical source location and, for ZIP inputs, the source member name."""

    source_path: Path
    member_name: str | None = None
    member_index: int | None = None

    @property
    def output_directory(self) -> Path:
        if self.member_name is not None:
            return self.source_path.parent / self.source_path.stem
        return self.source_path.parent

    @property
    def output_stem(self) -> str:
        if self.member_name is not None:
            return Path(self.member_name).stem
        return self.source_path.stem

    @property
    def display_name(self) -> str:
        if self.member_name is None:
            return self.source_path.name
        suffix = f", item {self.member_index + 1}" if self.member_index is not None else ""
        return f"{self.member_name} (from {self.source_path.name}{suffix})"


@dataclass(frozen=True)
class LoadedGPXFile:
    """A parsed GPX object together with its stable workspace path and provenance."""

    gpx: GPX
    origin: FileOrigin


try:
    from fastkml import kml
    from fastkml.containers import Document, Folder
    from fastkml.features import Placemark
    from pygeoif.geometry import LineString, Point

    KML_AVAILABLE = True
except ImportError:
    KML_AVAILABLE = False
    kml = Folder = Placemark = Document = LineString = Point = None


class GeoFileManager:
    """Load GPX, KML, and ZIP inputs as GPX objects."""

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger if logger else logging.getLogger(__name__)

    def _extract_gpx_kml_from_zip(
        self, zip_path: Path, temp_dir: Path
    ) -> list[tuple[Path, FileOrigin]]:
        """Extract supported files to a unique temporary location."""
        extracted_files = []
        archive_dir = temp_dir / zip_path.stem
        archive_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                for index, file_info in enumerate(zip_ref.infolist()):
                    if file_info.filename.lower().endswith((".gpx", ".kml")):
                        extracted_path = archive_dir / f"{index}_{Path(file_info.filename).name}"
                        extracted_path.write_bytes(zip_ref.read(file_info.filename))
                        extracted_files.append(
                            (
                                extracted_path,
                                FileOrigin(
                                    source_path=zip_path,
                                    member_name=Path(file_info.filename).name,
                                    member_index=index,
                                ),
                            )
                        )
            self.logger.info(f"Extracted {len(extracted_files)} GPX/KML files from {zip_path.name}")
        except (OSError, zipfile.BadZipFile, RuntimeError) as error:
            self.logger.error(f"Error extracting ZIP file {zip_path}: {error}")
            self.logger.debug(f"Full traceback:\n{traceback.format_exc()}")
        return extracted_files

    def _load_gpx_file(self, gpx_path: Path) -> GPX | None:
        """Load and parse a GPX file."""
        try:
            with gpx_path.open("r", encoding="utf-8") as file:
                gpx_data = gpxpy.parse(file)
                self.logger.info(f"Successfully loaded GPX file: {gpx_path.name}")
                return gpx_data
        except GPXXMLSyntaxException as error:
            self.logger.error(f"Error parsing GPX file {gpx_path.name}: {error}")
            return None
        except (OSError, UnicodeError, ValueError) as error:
            self.logger.error(f"Error loading GPX file {gpx_path.name}: {error}")
            self.logger.debug(f"Full traceback:\n{traceback.format_exc()}")
            return None

    def _load_kml_file(self, kml_path: Path) -> GPX | None:
        """Load and parse KML, converting supported geometries to GPX."""
        if not KML_AVAILABLE:
            self.logger.error("fastkml library is not available to process KML files.")
            return None

        try:
            parsed_kml = kml.KML.parse(kml_path)
            gpx = gpxpy.gpx.GPX()
            for feature in parsed_kml.features:
                self._process_kml_feature(feature, gpx)
            self.logger.info(f"Successfully loaded and converted KML file {kml_path.name} to GPX.")
            return gpx
        except (OSError, ValueError, TypeError, AttributeError) as error:
            self.logger.error(f"Error loading or converting KML file {kml_path.name}: {error}")
            self.logger.debug(f"Full traceback:\n{traceback.format_exc()}")
            return None

    def _process_kml_feature(self, feature, gpx: GPX) -> None:
        """Recursively convert supported KML placemarks."""
        if isinstance(feature, Placemark):
            if feature.geometry is None:
                return
            if isinstance(feature.geometry, Point):
                gpx.waypoints.append(
                    gpxpy.gpx.GPXWaypoint(
                        latitude=feature.geometry.y,
                        longitude=feature.geometry.x,
                        elevation=feature.geometry.z if feature.geometry.has_z else None,
                        name=feature.name,
                        description=feature.description,
                    )
                )
            elif isinstance(feature.geometry, LineString):
                track = gpxpy.gpx.GPXTrack(name=feature.name)
                segment = gpxpy.gpx.GPXTrackSegment()
                for coordinate in feature.geometry.coords:
                    segment.points.append(
                        gpxpy.gpx.GPXTrackPoint(
                            latitude=coordinate[1],
                            longitude=coordinate[0],
                            elevation=coordinate[2] if len(coordinate) > 2 else None,
                        )
                    )
                if segment.points:
                    track.segments.append(segment)
                    gpx.tracks.append(track)
        elif isinstance(feature, Document | Folder):
            for child in feature.features:
                self._process_kml_feature(child, gpx)

    def load_files_with_origins(self, file_paths: list[Path]) -> dict[Path, LoadedGPXFile]:
        """Load supported files and retain stable identities and source provenance."""
        loaded_files = {}
        with TemporaryDirectory(prefix="gpx_kml_converter_") as temp_path:
            temp_dir = Path(temp_path)
            all_files_to_process: list[tuple[Path, Path, FileOrigin]] = []

            for index, path in enumerate(file_paths):
                if path.suffix.lower() == ".zip":
                    for extracted_path, origin in self._extract_gpx_kml_from_zip(
                        path, temp_dir / f"archive_{index}"
                    ):
                        member_index = origin.member_index
                        member_name = origin.member_name
                        if member_index is None or member_name is None:
                            raise ValueError("ZIP member provenance is incomplete.")
                        workspace_path = (
                            path.parent
                            / f".{path.stem}.workspace"
                            / f"{member_index}_{Path(member_name).name}"
                        )
                        all_files_to_process.append((extracted_path, workspace_path, origin))
                else:
                    all_files_to_process.append((path, path, FileOrigin(path)))

            for file_path, workspace_path, origin in all_files_to_process:
                if file_path.suffix.lower() == ".gpx":
                    gpx_obj = self._load_gpx_file(file_path)
                elif file_path.suffix.lower() == ".kml":
                    gpx_obj = self._load_kml_file(file_path)
                else:
                    self.logger.warning(f"Unsupported file type for {file_path.name}. Skipping.")
                    continue

                if gpx_obj:
                    loaded_files[workspace_path] = LoadedGPXFile(gpx_obj, origin)

        return loaded_files

    def load_files(self, file_paths: list[Path]) -> dict[Path, GPX]:
        """Load GPX objects, preserving stable paths for ZIP members."""
        return {
            path: loaded.gpx for path, loaded in self.load_files_with_origins(file_paths).items()
        }
