"""GUI interface for python-template-project using tkinter with integrated logging.

This module provides a graphical user interface for the python-template-project
with settings dialog, file management, and centralized logging capabilities.

run gui: python -m python_template_project.gui
"""

import os
import subprocess
import sys
import threading
import tkinter as tk
import traceback
import webbrowser
from functools import partial
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import gpxpy  # Import gpxpy directly for metadata extraction

# Matplotlib imports for plotting
import matplotlib.pyplot as plt
from config_cli_gui.gui import SettingsDialogGenerator, ToolTip
from gpxpy.gpx import GPX
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from gpx_kml_converter.config.config import ProjectConfigManager
from gpx_kml_converter.core.base import BaseGPXProcessor, GeoFileManager  # Import GeoFileManager
from gpx_kml_converter.core.gpx_plotter import GPXPlotter
from gpx_kml_converter.core.logging import (
    connect_gui_logging,
    disconnect_gui_logging,
    get_logger,
    initialize_logging,
)


class GuiLogWriter:
    """Log writer that handles GUI text widget updates in a thread-safe way."""

    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.root = text_widget.winfo_toplevel()
        self.hyperlink_tags = {}  # To store clickable links

    def write(self, text):
        """Write text to the widget in a thread-safe manner."""
        # Schedule the GUI update in the main thread
        self.root.after(0, self._update_text, text)

    def _update_text(self, text):
        """Update the text widget (must be called from main thread)."""
        try:
            current_end = self.text_widget.index(tk.END)
            self.text_widget.insert(tk.END, text)

            # Check for a directory path (simplified regex for common path formats)
            # This regex looks for paths that start with a drive letter (C:\), a forward slash (/)
            # or a backslash (\) followed by word characters, and ends with a word character.
            # This is a basic approach; more robust path detection might be needed for edge cases.
            import re

            path_match = re.search(
                r"([A-Za-z]:[\\/][\S ]*|[\\][\\/][\S ]*|[\w/.-]+[/][\S ]*)\b", text
            )
            if path_match:
                path = path_match.group(0).strip()
                # Ensure the path exists and is a directory to make it clickable
                if Path(path).is_dir():
                    start_index = self.text_widget.search(path, current_end, tk.END)
                    if start_index:
                        end_index = f"{start_index}+{len(path)}c"
                        tag_name = f"link_{len(self.hyperlink_tags)}"
                        self.text_widget.tag_config(tag_name, foreground="blue", underline=True)
                        self.text_widget.tag_bind(
                            tag_name, "<Button-1>", lambda e, p=path: self._open_path_in_explorer(p)
                        )
                        self.text_widget.tag_bind(
                            tag_name, "<Enter>", lambda e: self.text_widget.config(cursor="hand2")
                        )
                        self.text_widget.tag_bind(
                            tag_name, "<Leave>", lambda e: self.text_widget.config(cursor="")
                        )
                        self.text_widget.tag_add(tag_name, start_index, end_index)
                        self.hyperlink_tags[tag_name] = path

            self.text_widget.see(tk.END)
            self.text_widget.update_idletasks()
        except tk.TclError:
            # Widget might be destroyed
            pass

    def _open_path_in_explorer(self, path):
        """Opens the given path in the file explorer."""
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            get_logger("gui.main").error(f"Failed to open path {path}: {e}")

    def flush(self):
        """Flush method for compatibility."""
        pass


class MainGui:
    """Main GUI application class."""

    processing_modes = [
        ("compress_files", "⏬", "Compress Files"),
        ("merge_files", "🔂", "Merge Files"),
        ("extract_pois", "📍", "Extract POIs from Tracks"),
    ]

    def __init__(self, root):
        self.root = root
        self.root.title("gpx-kml-converter")
        self.root.geometry("1400x800")  # Increased width and height for new layout

        # Initialize configuration
        self.config_manager = ProjectConfigManager("config.yaml")

        # Initialize logging system
        self.logger_manager = initialize_logging(self.config_manager)
        self.logger = get_logger("gui.main")

        # File lists - now hold Path to GPX object mapping
        self.gpx_input: dict[Path, GPX] = {}
        self.gpx_output: dict[Path, GPX] = {}
        self._last_selected_file_path = (
            None  # To store path of file currently shown in metadata/plot
        )

        # Initialize GeoFileManager
        self.geo_file_manager = GeoFileManager(logger=self.logger)

        # Matplotlib elements
        self.fig = None
        self.ax = None
        self.canvas = None
        self.toolbar = None
        self.fig1 = None
        self.ax1 = None
        self.canvas1 = None
        self.toolbar1 = None
        self.country_borders_gdf = None  # GeoDataFrame for country borders
        self.gpx_map_plotter = None  # New GPXPlotter instance
        self.gpx_profile_plotter = None  # New GPXPlotter instance
        self.log_window = None

        self._build_widgets()
        self._create_menu()

        # Setup GUI logging after widgets are created
        self._build_log_window()
        self._setup_gui_logging()

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.logger.info("GUI application started")
        self.logger_manager.log_config_summary()

        # Initialize GPXPlotter after country borders are loaded
        self.gpx_map_plotter = GPXPlotter(
            self.fig,
            self.ax,
            self.canvas,
            self.logger,
        )

        self.gpx_profile_plotter = GPXPlotter(
            self.fig1,
            self.ax1,
            self.canvas1,
            self.logger,
        )

    def _build_widgets(self):
        """Build the main GUI widgets."""
        # Main container frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Create main vertical PanedWindow for upper/lower sections
        main_vertical_paned = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        main_vertical_paned.pack(fill=tk.BOTH, expand=True)

        # Upper section
        main_upper = ttk.Frame(main_vertical_paned)
        main_vertical_paned.add(main_upper, weight=7)

        # Lower section
        main_lower = ttk.Frame(main_vertical_paned)
        main_vertical_paned.add(main_lower, weight=1)

        # Upper section horizontal layout
        upper_horizontal_paned = ttk.PanedWindow(main_upper, orient=tk.HORIZONTAL)
        upper_horizontal_paned.pack(fill=tk.BOTH, expand=True)

        # Files panel (left side of upper section)
        files_panel = ttk.Frame(upper_horizontal_paned)
        upper_horizontal_paned.add(files_panel, weight=1)

        # Plot frame (right side of upper section)
        plot_frame = ttk.LabelFrame(upper_horizontal_paned, text="Map Visualization")
        upper_horizontal_paned.add(plot_frame, weight=1)

        # Files panel horizontal layout
        files_horizontal_paned = ttk.PanedWindow(files_panel, orient=tk.HORIZONTAL)
        files_horizontal_paned.pack(fill=tk.BOTH, expand=True)

        # Input files frame (left in files panel)
        input_file_frame = ttk.LabelFrame(files_horizontal_paned, text="Input Files")
        files_horizontal_paned.add(input_file_frame, weight=1)

        # Button frame (middle in files panel) - fixed width 20 pixels
        button_frame = ttk.Frame(files_horizontal_paned)
        button_frame.configure(width=20)
        files_horizontal_paned.add(button_frame, weight=0)

        # Output files frame (right in files panel)
        output_file_frame = ttk.LabelFrame(files_horizontal_paned, text="Generated Files")
        files_horizontal_paned.add(output_file_frame, weight=1)

        # Lower section horizontal layout
        lower_horizontal_paned = ttk.PanedWindow(main_lower, orient=tk.HORIZONTAL)
        lower_horizontal_paned.pack(fill=tk.BOTH, expand=True)

        # Metadata frame (left in lower section)
        metadata_frame = ttk.LabelFrame(lower_horizontal_paned, text="File Metadata")
        lower_horizontal_paned.add(metadata_frame, weight=1)

        # Tracks listbox frame (middle in lower section)
        tracks_listbox_frame = ttk.LabelFrame(lower_horizontal_paned, text="Tracks")
        lower_horizontal_paned.add(tracks_listbox_frame, weight=1)

        # Profile plot frame (right in lower section)
        profile_plot_frame = ttk.LabelFrame(lower_horizontal_paned, text="Profile Plot")
        lower_horizontal_paned.add(profile_plot_frame, weight=1)

        # Build Input File list
        self._build_input_file_list(input_file_frame)

        # Build Output File list
        self._build_output_file_list(output_file_frame)

        # Build Button panel
        self._build_button_panel(button_frame)

        # Build Metadata display
        self._build_metadata_display(metadata_frame)

        # Build Matplotlib Plot
        self._build_plot_display(plot_frame)

        # Build Tracks listbox (placeholder for now)
        self._build_tracks_listbox(tracks_listbox_frame)

        # Build Profile plot (placeholder for now)
        self._build_profile_plot(profile_plot_frame)

    def _build_input_file_list(self, parent_frame):
        """Build the input file listbox with scrollbars."""
        self.input_file_listbox = self.__build_listbox(
            parent_frame, lambda event: self._on_file_selection(event, self.gpx_input)
        )
        self.input_file_listbox.bind(
            "<Double-Button-1>", lambda event: self._open_selected_file(event, self.gpx_input)
        )

    def _build_output_file_list(self, parent_frame):
        """Build the output file listbox with scrollbars."""
        self.output_file_listbox = self.__build_listbox(
            parent_frame, lambda event: self._on_file_selection(event, self.gpx_output)
        )
        self.output_file_listbox.bind(
            "<Double-Button-1>", lambda event: self._open_selected_file(event, self.gpx_output)
        )

    def _build_button_panel(self, parent_frame):
        """Build the button panel with fixed width."""
        # Configure fixed width
        parent_frame.pack_propagate(False)
        parent_frame.configure(width=30)

        open_button = ttk.Button(parent_frame, text="📂", command=self._open_files)
        ToolTip(open_button, "Open Files")
        open_button.pack(pady=8, fill=tk.X)

        self.run_buttons = {}
        for mode, label, tooltip in self.processing_modes:
            button = ttk.Button(
                parent_frame, text=label, command=partial(self._run_processing, mode=mode)
            )
            button.pack(pady=1, fill=tk.X)
            ToolTip(button, tooltip)
            self.run_buttons[mode] = button

        self.clear_files_button = ttk.Button(
            parent_frame,
            text="🗑️",
            command=self._clear_files,
        )
        ToolTip(self.clear_files_button, "Clear Files")
        self.clear_files_button.pack(pady=8, fill=tk.X)

        self.progress = ttk.Progressbar(parent_frame, mode="indeterminate")
        self.progress.pack(pady=0, fill=tk.X)

    def _build_metadata_display(self, parent_frame):
        """Build the metadata display with scrollbars."""
        # Frame für Text widget mit beiden Scrollbars
        metadata_text_frame = ttk.Frame(parent_frame)
        metadata_text_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self.metadata_text = tk.Text(metadata_text_frame, state=tk.DISABLED)

        # Vertikale Scrollbar
        metadata_v_scrollbar = ttk.Scrollbar(
            metadata_text_frame, orient="vertical", command=self.metadata_text.yview
        )
        self.metadata_text.configure(yscrollcommand=metadata_v_scrollbar.set)

        # Horizontale Scrollbar
        metadata_h_scrollbar = ttk.Scrollbar(
            metadata_text_frame, orient="horizontal", command=self.metadata_text.xview
        )
        self.metadata_text.configure(xscrollcommand=metadata_h_scrollbar.set)

        # Grid layout für Text widget und Scrollbars
        self.metadata_text.grid(row=0, column=0, sticky="nsew")
        metadata_v_scrollbar.grid(row=0, column=1, sticky="ns")
        metadata_h_scrollbar.grid(row=1, column=0, sticky="ew")

        metadata_text_frame.grid_rowconfigure(0, weight=1)
        metadata_text_frame.grid_columnconfigure(0, weight=1)

    def _build_plot_display(self, parent_frame):
        """Build the matplotlib plot display."""
        parent_frame.grid_rowconfigure(0, weight=1)  # Canvas
        parent_frame.grid_rowconfigure(1, weight=0)  # Toolbar
        parent_frame.grid_columnconfigure(0, weight=1)

        # Setup Matplotlib figure and canvas
        self.fig, self.ax = plt.subplots(figsize=(8, 4))  # Kleinere initiale Höhe
        self.fig.set_facecolor("#EEEEEE")  # Light grey background for the figure
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=0, column=0, sticky="nsew")

        # Add Matplotlib toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, parent_frame, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.grid(row=1, column=0, sticky="ew")  # Position toolbar below canvas
        self.canvas_widget.config(cursor="hand2")  # Change cursor when hovering over plot

    def _build_tracks_listbox(self, parent_frame):
        """Build the tracks listbox"""
        self.tracks_listbox = self.__build_listbox(
            parent_frame, lambda event: self._on_track_selection(event)
        )

    @staticmethod
    def __build_listbox(parent_frame, evt) -> tk.Listbox:
        tracks_listbox_frame = ttk.Frame(parent_frame)
        tracks_listbox_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        _listbox = tk.Listbox(tracks_listbox_frame, selectmode=tk.EXTENDED)

        # Vertikale Scrollbar
        input_file_v_scrollbar = ttk.Scrollbar(
            tracks_listbox_frame, orient="vertical", command=_listbox.yview
        )
        _listbox.configure(yscrollcommand=input_file_v_scrollbar.set)

        # Horizontale Scrollbar
        input_file_h_scrollbar = ttk.Scrollbar(
            tracks_listbox_frame, orient="horizontal", command=_listbox.xview
        )
        _listbox.configure(xscrollcommand=input_file_h_scrollbar.set)

        # Grid layout für Listbox und Scrollbars
        _listbox.grid(row=0, column=0, sticky="nsew")
        input_file_v_scrollbar.grid(row=0, column=1, sticky="ns")
        input_file_h_scrollbar.grid(row=1, column=0, sticky="ew")

        tracks_listbox_frame.grid_rowconfigure(0, weight=1)
        tracks_listbox_frame.grid_columnconfigure(0, weight=1)

        _listbox.bind("<<ListboxSelect>>", evt)
        return _listbox

    def _build_profile_plot(self, parent_frame):
        """Build the matplotlib plot display."""
        parent_frame.grid_rowconfigure(0, weight=1)  # Canvas
        parent_frame.grid_rowconfigure(1, weight=0)  # Toolbar
        parent_frame.grid_columnconfigure(0, weight=1)

        # Setup Matplotlib figure and canvas
        self.fig1, self.ax1 = plt.subplots(figsize=(8, 4))  # Kleinere initiale Höhe
        self.fig1.set_facecolor("#EEEEEE")  # Light grey background for the figure
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=parent_frame)
        self.canvas_widget1 = self.canvas1.get_tk_widget()
        self.canvas_widget1.grid(row=0, column=0, sticky="nsew")

        self.canvas_widget1.config(cursor="hand2")  # Change cursor when hovering over plot

    def _on_log_window_close(self):
        """Callback function when log window is closed."""
        if self.log_window:
            self.log_window.destroy()
        self.log_window = None

    def _build_log_window(self):
        """Build the log window as a separate window."""
        # Create log window
        if self.log_window is not None:
            return

        self.log_window = tk.Toplevel(self.root)
        self.log_window.title("Log Output")
        self.log_window.geometry("800x400")

        self.log_window.protocol("WM_DELETE_WINDOW", self._on_log_window_close)

        # Log frame
        log_frame = ttk.LabelFrame(self.log_window, text="Log Output")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        log_frame.grid_rowconfigure(0, weight=1)  # Text widget
        log_frame.grid_columnconfigure(0, weight=1)  # Text widget
        log_frame.grid_rowconfigure(1, weight=0)  # Controls

        # Frame für Log Text widget mit beiden Scrollbars
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        self.log_text = tk.Text(log_text_frame, height=15)  # Höher, kein Wrap

        # Vertikale Scrollbar
        log_v_scrollbar = ttk.Scrollbar(
            log_text_frame, orient="vertical", command=self.log_text.yview
        )
        self.log_text.configure(yscrollcommand=log_v_scrollbar.set)

        # Horizontale Scrollbar
        log_h_scrollbar = ttk.Scrollbar(
            log_text_frame, orient="horizontal", command=self.log_text.xview
        )
        self.log_text.configure(xscrollcommand=log_h_scrollbar.set)

        # Grid layout für Log Text widget und Scrollbars
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_v_scrollbar.grid(row=0, column=1, sticky="ns")
        log_h_scrollbar.grid(row=1, column=0, sticky="ew")

        log_text_frame.grid_rowconfigure(0, weight=1)
        log_text_frame.grid_columnconfigure(0, weight=1)

        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.grid(row=1, column=0, sticky="ew", padx=0, pady=0)

        ttk.Button(log_controls, text="Clear Log", command=self._clear_log).pack(side=tk.LEFT)

        ttk.Label(log_controls, text="Log Level:").pack(side=tk.LEFT, padx=0, pady=0)
        self.log_level_var = tk.StringVar(
            value=self.config_manager.get_category("app").log_level.default
        )
        log_level_combo = ttk.Combobox(
            log_controls,
            textvariable=self.log_level_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            state="readonly",
            width=10,
        )
        log_level_combo.pack(side=tk.LEFT)
        log_level_combo.bind("<<ComboboxSelected>>", self._on_log_level_changed)

    def _create_menu(self):
        """Create the application menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open...", command=self._open_files)
        file_menu.add_separator()
        # Create Run menu options dynamically
        for mode, _, tooltip in self.processing_modes:
            file_menu.add_command(label=tooltip, command=partial(self._run_processing, mode=mode))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)

        # Options menu
        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=options_menu)
        options_menu.add_command(label="Settings", command=self._open_settings)

        # View menu
        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=options_menu)
        options_menu.add_command(label="Show Log", command=self._build_log_window)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User help", command=self._open_help)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)

    def _setup_gui_logging(self):
        """Setup GUI logging integration."""
        # Create GUI log writer
        self.gui_log_writer = GuiLogWriter(self.log_text)
        # Connect to logging system
        connect_gui_logging(self.gui_log_writer)

    def _on_log_level_changed(self, event=None):
        """Handle log level change."""
        new_level = self.log_level_var.get()
        self.logger_manager.set_log_level(new_level)
        self.logger.info(f"Log level changed to {new_level}")

    def _clear_log(self):
        """Clear the log text widget."""
        self.log_text.delete(1.0, tk.END)
        self.logger.debug("Log display cleared")

    def _clear_files(self):
        """Clear the input file list."""
        self.gpx_input.clear()
        self.gpx_output.clear()
        self.output_file_listbox.delete(0, tk.END)
        self.input_file_listbox.delete(0, tk.END)
        self.tracks_listbox.delete(0, tk.END)
        self.logger.info("All file file lists cleared")
        self._clear_metadata_and_plot()  # Clear plot and metadata when output files are cleared

    def _remove_selected_input_files(self):
        """Remove selected files from the input file list."""
        selected_indices = self.input_file_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "No files selected to remove!")
            return

        # Get paths of selected files to remove from gpx_input dict
        paths_to_remove = []
        for i in reversed(selected_indices):
            listbox_item = self.input_file_listbox.get(i)
            # Assuming listbox item format is "filename (filepath)"
            path_str = listbox_item.split(" (")[-1].rstrip(")")
            paths_to_remove.append(Path(path_str))

            # If the removed file was the one currently displayed, clear metadata/plot
            if Path(path_str) == self._last_selected_file_path:
                self._clear_metadata_and_plot()
            self.input_file_listbox.delete(i)

        for path in paths_to_remove:
            if path in self.gpx_input:
                del self.gpx_input[path]

        self.logger.info(f"Removed {len(selected_indices)} selected input files.")

    def _on_file_selection(self, event, gpx_dict_source: dict[Path, GPX]):
        """Handle selection change in file listboxes to update metadata/plot."""
        widget = event.widget
        self._update_selected_file_display(widget, gpx_dict_source)

    def _on_track_selection(self, event):
        """Handle selection change in file listboxes to update metadata/plot."""
        listbox_widget = event.widget
        self._update_profile(listbox_widget)

    def _update_profile(self, listbox_widget):
        selected_indices = listbox_widget.curselection()
        if selected_indices:
            index = selected_indices[0]
            track_name = listbox_widget.get(index)
            # Plotting
            self.gpx_profile_plotter.plot_track_profile(self.selected_gpx, track_name)

    def _update_tracks(self, gpx_obj: GPX):
        """Separate logic to update display based on listbox selection."""
        new_tracks = [track.name for track in gpx_obj.tracks]
        if list(self.tracks_listbox.get(0, tk.END)) == new_tracks:
            return  # kein Update nötig

        self.tracks_listbox.delete(0, tk.END)
        self.selected_gpx = gpx_obj
        for track_name in new_tracks:
            self.tracks_listbox.insert(tk.END, track_name or "<Unnamed>")

    def _update_selected_file_display(self, listbox_widget, gpx_dict_source: dict[Path, GPX]):
        """Separate logic to update display based on listbox selection."""
        selected_indices = listbox_widget.curselection()
        if selected_indices:
            index = selected_indices[0]
            listbox_item = listbox_widget.get(index)
            file_path_str = listbox_item.split(" (")[-1].rstrip(")")
            self._parse_and_display_file(Path(file_path_str), gpx_dict_source)
        else:
            pass
            # do not clear map data if focus is lost
            # self._clear_metadata_and_plot()

    def _open_selected_file(self, event, gpx_dict_source: dict[Path, GPX]):
        """Opens the selected file in the system's default application or explorer.
        Also triggers parsing and display for the selected file."""
        selection_index = event.widget.nearest(event.y)
        if selection_index == -1:  # No item clicked
            return

        listbox_item = event.widget.get(selection_index)
        file_path_str = listbox_item.split(" (")[-1].rstrip(")")
        file_path = Path(file_path_str)

        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            messagebox.showerror("Error", f"File not found: {file_path}")
            return

        try:
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", file_path])
            else:
                subprocess.Popen(["xdg-open", file_path])
            self.logger.info(f"Opened file: {file_path.name}")
        except Exception as e:
            self.logger.error(f"Could not open file {file_path.name}: {e}")
            messagebox.showerror("Error", f"Could not open file {file_path.name}: {e}")

        # After opening, also parse and display it in the GUI
        self._parse_and_display_file(file_path, gpx_dict_source)

    def _open_files(self):
        """Open file dialog and add files to list."""
        file_paths = filedialog.askopenfilenames(
            title="Select input files",
            filetypes=[
                ("GPX/KML/ZIP files", "*.gpx *.kml *.zip"),
                ("GPX files", "*.gpx"),
                ("KML files", "*.kml"),
                ("ZIP archives", "*.zip"),
                ("All files", "*.*"),
            ],
        )
        if not file_paths:
            return

        new_files_loaded = 0
        file_paths_as_paths = [Path(fp) for fp in file_paths]

        # Use GeoFileManager to load files
        loaded_gpx_map = self.geo_file_manager.load_files(file_paths_as_paths)

        if not loaded_gpx_map:
            self.logger.warning("No GPX data could be loaded from the selected files.")
            messagebox.showinfo("Info", "No GPX data could be loaded from the selected files.")
            return

        for path, gpx_obj in loaded_gpx_map.items():
            if path not in self.gpx_input:
                self.gpx_input[path] = gpx_obj
                self.input_file_listbox.insert(tk.END, f"{path.name} ({path})")
                new_files_loaded += 1
            else:
                self.logger.info(f"File {path.name} already loaded. Skipping.")

        self.logger.info(f"Loaded {new_files_loaded} new GPX files.")
        if new_files_loaded > 0:
            self.input_file_listbox.selection_clear(0, tk.END)
            self.input_file_listbox.selection_set(0)
            self._update_selected_file_display(self.input_file_listbox, self.gpx_input)

    def _run_processing(self, mode: str):
        """Run the selected processing mode in a separate thread."""
        selected_indices = self.input_file_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one input file to process.")
            return

        selected_gpx_objects = []
        selected_file_paths = []  # Keep track of original paths for output naming if needed
        for index in selected_indices:
            listbox_item = self.input_file_listbox.get(index)
            file_path_str = listbox_item.split(" (")[-1].rstrip(")")
            file_path = Path(file_path_str)
            if file_path in self.gpx_input:
                selected_gpx_objects.append(self.gpx_input[file_path])
                selected_file_paths.append(file_path)
            else:
                self.logger.warning(
                    f"Selected file {file_path.name} not found in loaded GPX data. Skipping."
                )

        if not selected_gpx_objects:
            messagebox.showwarning("Warning", "No valid GPX objects selected for processing.")
            return

        for button in self.run_buttons.values():
            button.config(state=tk.DISABLED)
        self.clear_files_button.config(state=tk.DISABLED)
        self.progress.start()
        self.logger.info(f"Starting '{mode}' processing for {len(selected_gpx_objects)} files...")

        # Clear previous output files and listbox
        # self.gpx_output.clear()
        self.output_file_listbox.delete(0, tk.END)
        self._clear_metadata_and_plot()

        def processing_thread():
            try:
                processor = BaseGPXProcessor(
                    input_gpx_list=selected_gpx_objects,
                    output=self.config_manager.get_category("cli").output.default,
                    min_dist=self.config_manager.get_category("cli").min_dist.default,
                    date_format=self.config_manager.get_category("app").date_format.default,
                    elevation=self.config_manager.get_category("cli").elevation.default,
                    logger=self.logger,
                )

                if mode == "compress_files":
                    processed_gpx_map = processor.compress_files()
                elif mode == "merge_files":
                    # For merging, typically all selected files are merged into one output
                    # The processor should handle creating a single output GPX
                    processed_gpx_map = processor.merge_files()
                elif mode == "extract_pois":
                    processed_gpx_map = processor.extract_pois()
                else:
                    self.logger.error(f"Unknown processing mode: {mode}")
                    processed_gpx_map = {}

                # Update GUI after processing
                self.root.after(0, self._update_gui_after_processing, processed_gpx_map)

            except Exception as err:
                self.logger.error(f"Error during {mode} processing: {err}")
                self.logger.debug(f"Full traceback:\n{traceback.format_exc()}")
                self.root.after(
                    0, lambda e=err: messagebox.showerror("Error", f"Processing failed: {e}")
                )
            finally:
                self.root.after(0, self._reset_ui_state)

        threading.Thread(target=processing_thread).start()

    def _update_gui_after_processing(self, processed_gpx_map: dict[Path, GPX]):
        """Update GUI elements after processing is complete (refactored version)."""
        self.gpx_output.update(processed_gpx_map)
        if processed_gpx_map:
            for path in processed_gpx_map.keys():
                self.output_file_listbox.insert(tk.END, f"{path.name} ({path})")

            self.output_file_listbox.selection_clear(0, tk.END)
            self.output_file_listbox.selection_set(tk.END)

            # Direkt die extrahierte Logik aufrufen
            self._update_selected_file_display(self.output_file_listbox, self.gpx_output)

    def _reset_ui_state(self):
        """Reset UI elements after processing completes or fails."""
        self.progress.stop()
        for button in self.run_buttons.values():
            button.config(state=tk.NORMAL)
        self.clear_files_button.config(state=tk.NORMAL)

    def _parse_and_display_file(self, file_path: Path, gpx_dict_source: dict[Path, GPX]):
        """Parse the selected GPX/KML file and display its metadata and plot."""
        self._clear_metadata_and_plot()
        self._last_selected_file_path = file_path

        gpx_obj = gpx_dict_source.get(file_path)

        if not gpx_obj:
            self.logger.error(f"GPX object not found for path: {file_path}")
            self.metadata_text.config(state=tk.NORMAL)
            self.metadata_text.insert(
                tk.END, f"Error: Could not load GPX data for {file_path.name}\n"
            )
            self.metadata_text.config(state=tk.DISABLED)
            return

        self.logger.info(f"Displaying metadata and plot for: {file_path.name}")
        self._display_gpx_metadata(gpx_obj, file_path.name)

        # Plotting
        self.gpx_map_plotter.plot_gpx_map(gpx_obj)

    def _display_gpx_metadata(self, gpx_obj: GPX, file_name: str):
        """Display metadata for the given GPX object."""
        self._update_tracks(gpx_obj)
        self.metadata_text.config(state=tk.NORMAL)
        self.metadata_text.delete(1.0, tk.END)  # Clear previous content

        self.metadata_text.insert(tk.END, f"File: {file_name}\n\n")
        self.metadata_text.insert(tk.END, "--- GPX Metadata ---\n")
        self.metadata_text.insert(tk.END, f"Creator: {gpx_obj.creator or 'N/A'}\n")

        if gpx_obj.name:
            self.metadata_text.insert(tk.END, f"Name: {gpx_obj.name}\n")
        if gpx_obj.description:
            self.metadata_text.insert(tk.END, f"Description: {gpx_obj.description}\n")

        self.metadata_text.insert(tk.END, "\n--- Tracks ---\n")
        if not gpx_obj.tracks:
            self.metadata_text.insert(tk.END, "No tracks found.\n")
        for i, track in enumerate(gpx_obj.tracks):
            track_name = track.name or f"Track {i + 1}"
            distance_2d = track.length_2d()
            self.metadata_text.insert(tk.END, f"  - {track_name}: {distance_2d / 1000:.1f} km")

            uphill, downhill = None, None
            try:
                # Temporary track for elevation calculation
                temp_track = gpxpy.gpx.GPXTrack()
                for segment in track.segments:
                    temp_segment = gpxpy.gpx.GPXTrackSegment()
                    temp_segment.points.extend(segment.points)
                    temp_track.segments.append(temp_segment)

                if temp_track.segments:
                    up_down = temp_track.get_uphill_downhill()
                    uphill = up_down.uphill
                    downhill = up_down.downhill
            except Exception as err:
                self.logger.debug(
                    f"Could not calculate uphill/downhill for track {track_name}: {err}"
                )

            if uphill is not None and downhill is not None:
                self.metadata_text.insert(tk.END, f" (↑{uphill:.0f}m ↓{downhill:.0f}m)\n")
            else:
                self.metadata_text.insert(tk.END, "\n")

        self.metadata_text.insert(tk.END, "\n--- Routes ---\n")
        if not gpx_obj.routes:
            self.metadata_text.insert(tk.END, "No routes found.\n")
        for i, route in enumerate(gpx_obj.routes):
            route_name = route.name or f"Route {i + 1}"
            distance_2d = route.length_2d()
            self.metadata_text.insert(tk.END, f"  - {route_name}: {distance_2d / 1000:.2f} km")

            uphill, downhill = None, None
            try:
                # Temporary track for elevation calculation
                temp_track = gpxpy.gpx.GPXTrack()
                temp_segment = gpxpy.gpx.GPXTrackSegment()
                temp_segment.points.extend(route.points)
                temp_track.segments.append(temp_segment)
                up_down = temp_track.get_uphill_downhill()
                uphill = up_down.uphill
                downhill = up_down.downhill
            except Exception as err:
                self.logger.debug(
                    f"Could not calculate uphill/downhill for route {route_name}: {err}"
                )

            if uphill is not None and downhill is not None:
                self.metadata_text.insert(tk.END, f" (↑{uphill:.1f}m ↓{downhill:.1f}m)\n")
            else:
                self.metadata_text.insert(tk.END, "\n")

        self.metadata_text.insert(tk.END, "\n--- Waypoints ---\n")
        if not gpx_obj.waypoints:
            self.metadata_text.insert(tk.END, "No waypoints found.\n")
        for i, waypoint in enumerate(gpx_obj.waypoints):
            waypoint_name = waypoint.name or f"Waypoint {i + 1}"
            self.metadata_text.insert(
                tk.END,
                f"  - {waypoint_name}: Lat {waypoint.latitude:.4f}, Lon {waypoint.longitude:.4f}",
            )
            if waypoint.elevation is not None:
                self.metadata_text.insert(tk.END, f", Alt {waypoint.elevation:.1f}m\n")
            else:
                self.metadata_text.insert(tk.END, "\n")

        self.metadata_text.insert(tk.END, "\n")

        self.metadata_text.config(state=tk.DISABLED)  # Disable editing

    def _clear_metadata_and_plot(self):
        """Clear the metadata text area and the plot."""
        self.metadata_text.config(state=tk.NORMAL)
        self.metadata_text.delete(1.0, tk.END)
        self.metadata_text.config(state=tk.DISABLED)
        self.gpx_map_plotter.clear_plot()
        """ self.gpx_profile_plotter.clear_plot() """
        self._last_selected_file_path = None

    def _open_settings(self):
        """Open the settings dialog."""
        self.logger.debug("Opening settings dialog")
        settings_dialog_generator = SettingsDialogGenerator(self.config_manager)
        dialog = settings_dialog_generator.create_settings_dialog(self.root)
        self.root.wait_window(dialog.dialog)

        if dialog.result == "ok":
            self.logger.info("Settings updated successfully")
            # Update log level selector if it changed
            self.log_level_var.set(self.config_manager.get_category("app").log_level.default)

    def _open_help(self):
        """Open the help documentation."""
        help_url = "https://gpx-kml-converter.readthedocs.io/en/stable/"
        if help_url:
            try:
                webbrowser.open(help_url)
                self.logger.info(f"Opened help documentation: {help_url}")
            except Exception as e:
                self.logger.error(f"Could not open help URL {help_url}: {e}")
                messagebox.showerror("Error", f"Could not open help documentation: {e}")
        else:
            self.logger.warning("Help URL not configured.")
            messagebox.showinfo("Info", "Help URL is not configured.")

    def _show_about(self):
        """Display about information."""
        __version__ = "0.1.0"  # Assuming a version number, replace if dynamic
        about_message = (
            f"gpx-kml-converter GUI Application\n"
            f"Version: {__version__}\n"
            f"Developed by: Your Name/Organization\n"
            f"Description: A tool to process and visualize GPX/KML files."
        )
        messagebox.showinfo("About gpx-kml-converter", about_message)
        self.logger.info("About dialog displayed.")

    def _on_closing(self):
        """Handle application closing."""
        self.logger.info("Shutting down GUI application.")
        disconnect_gui_logging()
        self.root.quit()
        self.root.destroy()


def main():
    """Main entry point for the GUI application."""
    root = tk.Tk()
    try:
        MainGui(root)
        root.mainloop()
    except Exception as e:
        # Catch any unhandled exceptions to log them before exiting
        logger = get_logger("gui.main")
        logger.critical(f"Unhandled exception in main GUI loop: {e}")
        logger.critical(f"Full traceback:\n{traceback.format_exc()}")
        messagebox.showerror(
            "Critical Error",
            f"An unhandled error occurred: {e}\nPlease check the log for details.",
        )
    finally:
        # Ensure logging is disconnected even if an error occurs
        disconnect_gui_logging()


if __name__ == "__main__":
    main()
