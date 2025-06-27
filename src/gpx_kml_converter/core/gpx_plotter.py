import math
from pathlib import Path

from gpxpy.gpx import GPX

# Geopandas and shapely for geographical data handling
try:
    import geopandas as gpd
    from shapely.geometry import LineString, Point

    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False
    gpd = None
    Point = None
    LineString = None
    print("Warning: geopandas not available. Plotting functionality will be limited.")


class GPXPlotter:
    """
    Handles plotting of GPX data on a Matplotlib canvas within a Tkinter application.
    Provides methods for zooming, panning, and adjusting the map view to fit data or window size.
    """

    def __init__(self, fig, ax, canvas, logger):
        self.fig = fig
        self.ax = ax
        self.canvas = canvas
        self.logger = logger
        self.country_borders_gdf = self._load_shape_files()

        # Initial view limits (e.g., Europe)
        self.current_xlim = (-10, 30)
        self.current_ylim = (35, 65)

        self.zoom_factor = 1.2
        self.is_panning = False
        self.pan_start_x = None
        self.pan_start_y = None

        self._connect_mpl_events()
        self._setup_axes()

    def _setup_axes(self):
        """Sets up initial plot properties for the axes."""
        self.ax.set_facecolor("#EEEEEE")  # Light grey background for the axes
        self.ax.tick_params(
            left=False, right=False, labelleft=False, labelbottom=False, bottom=False
        )  # Hide axis labels and ticks
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.set_xlim(self.current_xlim)
        self.ax.set_ylim(self.current_ylim)
        self.canvas.draw_idle()

    def _load_shape_files(self):
        """Load country borders once at startup if geopandas is available."""
        country_borders_gdf = None
        if GEOPANDAS_AVAILABLE:
            try:
                # Assuming the shapefile is relative to the script's location or project root
                # Adjust based on actual project structure.
                # Path from gui.py to project root is ../../../
                script_dir = Path(__file__).parent.parent.parent.parent
                shp_path = (
                    script_dir
                    / "res"
                    / "maps"
                    / "ne_50m_admin_0_countries"
                    / "ne_50m_admin_0_countries.shp"
                )
                if shp_path.exists():
                    country_borders_gdf = gpd.read_file(shp_path)
                    self.logger.info(f"Loaded country borders from: {shp_path}")
                else:
                    self.logger.warning(f"Country borders shapefile not found at: {shp_path}")
            except Exception as e:
                self.logger.error(f"Error loading country borders shapefile: {e}")
        else:
            self.logger.warning("Geopandas is not available. Cannot load country borders.")

        return country_borders_gdf

    def _connect_mpl_events(self):
        """Connects Matplotlib events to custom handlers."""
        self.canvas.mpl_connect("scroll_event", self._on_scroll)
        self.canvas.mpl_connect("button_press_event", self._on_button_press)
        self.canvas.mpl_connect("button_release_event", self._on_button_release)
        self.canvas.mpl_connect("motion_notify_event", self._on_mouse_motion)
        self.canvas.mpl_connect("resize_event", self._on_resize)  # Connect resize event

    def _on_scroll(self, event):
        """Handles mouse wheel scrolling for zooming."""
        if event.inaxes == self.ax:
            xdata, ydata = event.xdata, event.ydata
            if xdata is None or ydata is None:  # Sometimes event.xdata/ydata can be None
                return

            cur_xlim = self.ax.get_xlim()
            cur_ylim = self.ax.get_ylim()

            if event.button == "up":  # Zoom in
                scale_factor = 1 / self.zoom_factor
            elif event.button == "down":  # Zoom out
                scale_factor = self.zoom_factor
            else:
                return

            # Calculate new limits
            new_xlim = [
                xdata - (xdata - cur_xlim[0]) * scale_factor,
                xdata + (cur_xlim[1] - xdata) * scale_factor,
            ]
            new_ylim = [
                ydata - (ydata - cur_ylim[0]) * scale_factor,
                ydata + (cur_ylim[1] - ydata) * scale_factor,
            ]

            self.ax.set_xlim(new_xlim)
            self.ax.set_ylim(new_ylim)
            self.current_xlim = new_xlim
            self.current_ylim = new_ylim
            self.canvas.draw_idle()
            self.logger.debug(
                f"Zoomed {'in' if event.button == 'up' else 'out'} to {new_xlim}, {new_ylim}"
            )

    def _on_button_press(self, event):
        """Handles mouse button press for panning."""
        if event.inaxes == self.ax and event.button == 1:  # Left mouse button
            self.is_panning = True
            self.pan_start_x = event.xdata
            self.pan_start_y = event.ydata
            self.canvas.get_tk_widget().config(cursor="fleur")  # Change cursor to move
            self.logger.debug("Panning started.")

    def _on_button_release(self, event):
        """Handles mouse button release, ending panning."""
        if event.button == 1:
            self.is_panning = False
            self.canvas.get_tk_widget().config(cursor="hand2")  # Reset cursor
            self.logger.debug("Panning ended.")

    def _on_mouse_motion(self, event):
        """Handles mouse motion for panning."""
        if (
            self.is_panning
            and event.inaxes == self.ax
            and event.xdata is not None
            and event.ydata is not None
        ):
            dx = self.pan_start_x - event.xdata
            dy = self.pan_start_y - event.ydata

            cur_xlim = self.ax.get_xlim()
            cur_ylim = self.ax.get_ylim()

            new_xlim = [cur_xlim[0] + dx, cur_xlim[1] + dx]
            new_ylim = [cur_ylim[0] + dy, cur_ylim[1] + dy]

            self.ax.set_xlim(new_xlim)
            self.ax.set_ylim(new_ylim)
            self.current_xlim = new_xlim
            self.current_ylim = new_ylim
            self.canvas.draw_idle()

    def _on_resize(self, event):
        """Handles resize events for the Matplotlib figure."""
        # This function is called by Matplotlib's resize_event.
        # It ensures the plot updates when the Tkinter canvas changes size.
        self.logger.debug(
            f"Matplotlib figure resized to {self.fig.get_size_inches() * self.fig.dpi}"
        )
        # Redraw the canvas to apply the new size
        self.canvas.draw_idle()
        # Re-adjust limits if needed after resize, though Matplotlib usually handles aspect ratio.
        # If the plot becomes distorted, we might need a more complex `set_aspect` call here.

    def _clear_axes_common(self):
        """Common axes clearing and setup functionality."""
        self.ax.clear()
        self.ax.set_facecolor("#EEEEEE")

    def _calculate_distance(self, point1, point2):
        """
        Calculate the distance between two GPS points using the Haversine formula.
        Returns distance in kilometers.
        """
        if not all([point1.latitude, point1.longitude, point2.latitude, point2.longitude]):
            return 0.0

        lat1, lon1 = math.radians(point1.latitude), math.radians(point1.longitude)
        lat2, lon2 = math.radians(point2.latitude), math.radians(point2.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        # Earth's radius in kilometers
        r = 6371.0
        return r * c

    def _get_optimal_grid_spacing(self, data_range, target_divisions=8):
        """
        Calculate optimal grid spacing for given data range.
        Returns a "nice" number for grid spacing.
        """
        if data_range <= 0:
            return 1

        # Calculate rough step size
        rough_step = data_range / target_divisions

        # Find the magnitude (power of 10)
        magnitude = 10 ** math.floor(math.log10(rough_step))

        # Normalize the rough step to be between 1 and 10
        normalized = rough_step / magnitude

        # Choose a "nice" number
        if normalized <= 1:
            nice_step = 1
        elif normalized <= 2:
            nice_step = 2
        elif normalized <= 5:
            nice_step = 5
        else:
            nice_step = 10

        return nice_step * magnitude

    def _setup_distance_grid(self, max_distance_km):
        """Setup grid for distance axis (X-axis) with appropriate spacing."""
        # Choose spacing based on total distance
        if max_distance_km <= 12:
            spacing = 1
        elif max_distance_km <= 20:
            spacing = 2
        elif max_distance_km <= 60:
            spacing = 5
        elif max_distance_km <= 120:
            spacing = 10
        elif max_distance_km <= 600:
            spacing = 50
        else:
            spacing = 100

        return spacing

    def _setup_elevation_grid(self, min_elevation, max_elevation):
        """Setup grid for elevation axis (Y-axis) with appropriate spacing."""
        elevation_range = max_elevation - min_elevation

        if elevation_range <= 120:
            spacing = 10
        elif elevation_range <= 600:
            spacing = 50
        elif elevation_range <= 1200:
            spacing = 100
        elif elevation_range <= 2500:
            spacing = 200
        else:
            spacing = 500

        return spacing

    def _find_track_by_name(self, gpx_data: GPX, track_name: str):
        """Find a specific track by name in GPX data."""
        for track in gpx_data.tracks:
            if track.name == track_name:
                return track
        return None

    def plot_gpx_map(self, gpx_data: GPX):
        """Plots GPX data (tracks, routes, waypoints) on the Matplotlib canvas."""
        self._clear_axes_common()

        # Plot country borders if loaded
        if self.country_borders_gdf is not None:
            self.country_borders_gdf.plot(
                ax=self.ax, color="lightgray", edgecolor="darkgray", linewidth=0.5
            )

        all_points_coords = []  # Store (lon, lat) for setting limits

        # Plot Tracks
        for track in gpx_data.tracks:
            for segment in track.segments:
                if segment.points:
                    lats = [p.latitude for p in segment.points if p.latitude is not None]
                    lons = [p.longitude for p in segment.points if p.longitude is not None]
                    if lats and lons:
                        self.ax.plot(
                            lons, lats, color="darkblue", linewidth=1.5, zorder=2
                        )  # Dark blue for tracks
                        all_points_coords.extend(zip(lons, lats))

        # Plot Routes
        for route in gpx_data.routes:
            if route.points:
                lats = [p.latitude for p in route.points if p.latitude is not None]
                lons = [p.longitude for p in route.points if p.longitude is not None]
                if lats and lons:
                    self.ax.plot(
                        lons, lats, color="darkblue", linewidth=1.5, linestyle="--", zorder=2
                    )  # Dark blue, dashed for routes
                    all_points_coords.extend(zip(lons, lats))

        # Plot Waypoints
        waypoint_lons = [p.longitude for p in gpx_data.waypoints if p.longitude is not None]
        waypoint_lats = [p.latitude for p in gpx_data.waypoints if p.latitude is not None]
        if waypoint_lons and waypoint_lats:
            self.ax.scatter(
                waypoint_lons, waypoint_lats, color="red", s=10, zorder=3
            )  # Red small dots for waypoints
            all_points_coords.extend(zip(waypoint_lons, waypoint_lats))

        # Auto-adjust limits based on plotted data, or set default if no data
        self._set_plot_limits_map(all_points_coords)

        self.ax.set_aspect("equal", adjustable="box")  # Maintain aspect ratio
        self.ax.tick_params(
            left=False, right=False, labelleft=False, labelbottom=False, bottom=False
        )  # Hide axis labels and ticks
        self.canvas.draw()  # Redraw the canvas

    def plot_track_profile(self, gpx_data: GPX, track_name: str):
        """
        Plots elevation profile of a specific track.
        X-axis: Distance in kilometers
        Y-axis: Elevation in meters
        """
        # Find the specific track
        track = self._find_track_by_name(gpx_data, track_name)
        if not track:
            self.logger.warning(f"Track '{track_name}' not found in GPX data.")
            self.clear_plot()
            return

        # Collect all points from all segments of the track
        all_points = []
        for segment in track.segments:
            all_points.extend(segment.points)

        if not all_points:
            self.logger.warning(f"No points found in track '{track_name}'.")
            self.clear_plot()
            return

        # Filter points with valid coordinates and elevation
        valid_points = [
            p
            for p in all_points
            if p.latitude is not None and p.longitude is not None and p.elevation is not None
        ]

        if len(valid_points) < 2:
            self.logger.warning(
                f"Not enough valid points with elevation data in track '{track_name}'."
            )
            self.clear_plot()
            return

        # Calculate cumulative distances and collect elevations
        distances = [0.0]  # Start with 0 km
        elevations = [valid_points[0].elevation]

        cumulative_distance = 0.0
        for i in range(1, len(valid_points)):
            distance = self._calculate_distance(valid_points[i - 1], valid_points[i])
            cumulative_distance += distance
            distances.append(cumulative_distance)
            elevations.append(valid_points[i].elevation)

        # Clear and setup axes for profile plot
        self._clear_axes_common()

        # Plot the elevation profile
        self.ax.plot(distances, elevations, color="darkgreen", linewidth=2, zorder=2)
        self.ax.fill_between(distances, elevations, alpha=0.3, color="lightgreen", zorder=1)

        # Setup grid
        max_distance = max(distances) if distances else 1
        min_elevation = min(elevations) - 10 if elevations else 0
        max_elevation = max(elevations) + 10 if elevations else 100

        # Distance grid (X-axis)
        distance_spacing = self._setup_distance_grid(max_distance)
        distance_ticks = []
        distance = 0
        while distance <= max_distance:
            distance_ticks.append(distance)
            distance += distance_spacing

        # Elevation grid (Y-axis)
        elevation_spacing = self._setup_elevation_grid(min_elevation, max_elevation)
        # Round to nearest grid lines
        min_elevation_grid = math.floor(min_elevation / elevation_spacing) * elevation_spacing
        max_elevation_grid = math.ceil(max_elevation / elevation_spacing) * elevation_spacing

        elevation_ticks = []
        elevation = min_elevation_grid
        while elevation <= max_elevation_grid:
            elevation_ticks.append(elevation)
            elevation += elevation_spacing

        # Configure axes
        self.ax.set_xlim(0, max_distance * 1.02)  # Small buffer
        self.ax.set_ylim(min_elevation_grid, max_elevation_grid)

        # Set grid
        self.ax.set_xticks(distance_ticks)
        self.ax.set_yticks(elevation_ticks)
        self.ax.grid(True, alpha=0.3, linestyle="-", linewidth=0.5)

        # Labels and formatting
        self.ax.set_xlabel("Distance (km)", fontsize=10)
        self.ax.set_ylabel("Height (m)", fontsize=10)
        self.ax.set_title(f"Elevation profile: {track_name}", fontsize=12, fontweight="bold")

        # Show axis labels and ticks for profile
        self.ax.tick_params(left=True, right=False, labelleft=True, labelbottom=True, bottom=True)

        # Don't maintain equal aspect ratio for profile plots
        self.ax.set_aspect("auto")

        # Update current limits for zoom/pan functionality
        self.current_xlim = (0, max_distance * 1.02)
        self.current_ylim = (min_elevation_grid, max_elevation_grid)

        self.canvas.draw()
        self.logger.info(
            f"Plotted elevation profile for track '{track_name}' "
            f"({len(valid_points)} points, {max_distance:.1f} km total distance)"
        )

    def _set_plot_limits_map(self, all_points_coords):
        """
        Sets the plot limits for map view based on the provided coordinates or a default view.
        Adds a buffer and ensures aspect ratio is maintained for better visualization.
        """
        if all_points_coords:
            all_lons = [coord[0] for coord in all_points_coords]
            all_lats = [coord[1] for coord in all_points_coords]

            min_lat = min(all_lats)
            max_lat = max(all_lats)
            min_lon = min(all_lons)
            max_lon = max(all_lons)

            # Calculate initial range for buffering
            lat_range = max_lat - min_lat
            lon_range = max_lon - min_lon

            # Add a small buffer around the points for better visualization
            # Ensure a minimal range if data points are very close or single
            buffer_factor = 0.1
            min_buffer_deg = 0.05  # Minimum buffer in degrees if range is very small

            lat_buffer = max(lat_range * buffer_factor, min_buffer_deg if lat_range < 0.1 else 0)
            lon_buffer = max(lon_range * buffer_factor, min_buffer_deg if lon_range < 0.1 else 0)

            # Adjust limits
            self.current_xlim = (min_lon - lon_buffer, max_lon + lon_buffer)
            self.current_ylim = (min_lat - lat_buffer, max_lat + lat_buffer)

            # Ensure minimal extension if only one point or very small spread
            if (
                lat_range < 0.001 and lon_range < 0.001
            ):  # Very small range, likely a single point or few very close
                center_lat = (min_lat + max_lat) / 2
                center_lon = (min_lon + max_lon) / 2
                # Set a fixed small square around the point
                extension = 0.1  # e.g., 0.1 degrees around the point
                self.current_xlim = (center_lon - extension, center_lon + extension)
                self.current_ylim = (center_lat - extension, center_lat + extension)

        else:
            # Default view if no data is plotted (e.g., world map or Europe)
            self.current_xlim = (-10, 30)  # Default to a Europe-ish view
            self.current_ylim = (35, 65)

        self.ax.set_xlim(self.current_xlim)
        self.ax.set_ylim(self.current_ylim)
        self.ax.set_aspect("equal", adjustable="box")
        self.canvas.draw_idle()

    def clear_plot(self):
        """Clears the matplotlib plot."""
        self._clear_axes_common()
        self.ax.tick_params(
            left=False, right=False, labelleft=False, labelbottom=False, bottom=False
        )
        self.ax.set_aspect("equal", adjustable="box")
        # Reset to default view when cleared
        self.ax.set_xlim(-10, 30)
        self.ax.set_ylim(35, 65)
        self.current_xlim = (-10, 30)
        self.current_ylim = (35, 65)
        self.canvas.draw_idle()
