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

        # Set initial plot properties
        self.ax.set_facecolor("#EEEEEE")  # Light grey background for the axes
        self.ax.tick_params(
            left=False, right=False, labelleft=False, labelbottom=False, bottom=False
        )  # Hide axis labels and ticks
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.set_xlim(self.current_xlim)
        self.ax.set_ylim(self.current_ylim)
        self.canvas.draw_idle()

    def _load_shape_files(self):
        # Load country borders once at startup if geopandas is available
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

    def plot_gpx_data(self, gpx_data: GPX):
        """Plots GPX data (tracks, routes, waypoints) on the Matplotlib canvas."""
        self.ax.clear()  # Clear existing plot
        self.ax.set_facecolor("#EEEEEE")  # Light grey background for the axes

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
        self._set_plot_limits(all_points_coords)

        self.ax.set_aspect("equal", adjustable="box")  # Maintain aspect ratio
        self.ax.tick_params(
            left=False, right=False, labelleft=False, labelbottom=False, bottom=False
        )  # Hide axis labels and ticks
        self.canvas.draw()  # Redraw the canvas

    def _set_plot_limits(self, all_points_coords):
        """
        Sets the plot limits based on the provided coordinates or a default view.
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
        self.ax.clear()
        self.ax.set_facecolor("#EEEEEE")
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
