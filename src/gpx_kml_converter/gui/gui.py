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

# Matplotlib imports for plotting
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

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


import gpxpy  # Import gpxpy directly for metadata extraction
from config_cli_gui.gui import SettingsDialogGenerator

from gpx_kml_converter.config.config import ProjectConfigManager
from gpx_kml_converter.core.base import BaseGPXProcessor
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
        ("compress_files", "Compress"),
        ("merge_files", "Merge"),
        ("extract_pois", "Extract POIs"),
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

        # File lists
        self.input_files = []
        self.output_files = []
        self._last_selected_file_path = (
            None  # To store path of file currently shown in metadata/plot
        )

        # Matplotlib elements
        self.fig = None
        self.ax = None
        self.canvas = None
        self.toolbar = None
        self.country_borders_gdf = None  # GeoDataFrame for country borders

        self._build_widgets()
        self._create_menu()

        # Setup GUI logging after widgets are created
        self._setup_gui_logging()

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.logger.info("GUI application started")
        self.logger_manager.log_config_summary()

        # Load country borders once at startup if geopandas is available
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
                    self.country_borders_gdf = gpd.read_file(shp_path)
                    self.logger.info(f"Loaded country borders from: {shp_path}")
                else:
                    self.logger.warning(f"Country borders shapefile not found at: {shp_path}")
            except Exception as e:
                self.logger.error(f"Error loading country borders shapefile: {e}")
                self.country_borders_gdf = None

    def _build_widgets(self):
        """Build the main GUI widgets."""
        # Main container frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=0)

        # Create main PanedWindow for horizontal resizing
        main_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)

        # Left pane: Input files
        left_pane = ttk.Frame(main_paned)
        main_paned.add(left_pane, weight=1)

        # Middle pane: Contains buttons, metadata, and plot
        middle_pane = ttk.Frame(main_paned)
        main_paned.add(middle_pane, weight=2)

        # Right pane: Output files
        right_pane = ttk.Frame(main_paned)
        main_paned.add(right_pane, weight=1)

        # Vertical PanedWindow for middle section (buttons/metadata vs plot vs log)
        middle_vertical_paned = ttk.PanedWindow(middle_pane, orient=tk.VERTICAL)
        middle_vertical_paned.pack(fill=tk.BOTH, expand=True)

        # Top section of middle pane (buttons and metadata)
        middle_top_frame = ttk.Frame(middle_vertical_paned)
        middle_vertical_paned.add(middle_top_frame, weight=2)

        # Plot section
        plot_frame = ttk.LabelFrame(middle_vertical_paned, text="Map Visualization")
        middle_vertical_paned.add(plot_frame, weight=2)

        # Log section (höher als Plot)
        log_frame = ttk.LabelFrame(middle_vertical_paned, text="Log Output")
        middle_vertical_paned.add(log_frame, weight=3)

        # Input File list (Left Pane)
        input_file_frame = ttk.LabelFrame(left_pane, text="Input Files")
        input_file_frame.pack(fill=tk.BOTH, expand=True)

        # Frame für Listbox mit beiden Scrollbars
        input_listbox_frame = ttk.Frame(input_file_frame)
        input_listbox_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self.input_file_listbox = tk.Listbox(input_listbox_frame, selectmode=tk.EXTENDED)

        # Vertikale Scrollbar
        input_file_v_scrollbar = ttk.Scrollbar(
            input_listbox_frame, orient="vertical", command=self.input_file_listbox.yview
        )
        self.input_file_listbox.configure(yscrollcommand=input_file_v_scrollbar.set)

        # Horizontale Scrollbar
        input_file_h_scrollbar = ttk.Scrollbar(
            input_listbox_frame, orient="horizontal", command=self.input_file_listbox.xview
        )
        self.input_file_listbox.configure(xscrollcommand=input_file_h_scrollbar.set)

        # Grid layout für Listbox und Scrollbars
        self.input_file_listbox.grid(row=0, column=0, sticky="nsew")
        input_file_v_scrollbar.grid(row=0, column=1, sticky="ns")
        input_file_h_scrollbar.grid(row=1, column=0, sticky="ew")

        input_listbox_frame.grid_rowconfigure(0, weight=1)
        input_listbox_frame.grid_columnconfigure(0, weight=1)

        self.input_file_listbox.bind(
            "<Double-Button-1>", lambda event: self._open_selected_file(event, self.input_files)
        )
        self.input_file_listbox.bind(
            "<<ListboxSelect>>", lambda event: self._on_file_selection(event, self.input_files)
        )

        # Output File list (Right Pane)
        output_file_frame = ttk.LabelFrame(right_pane, text="Generated Files")
        output_file_frame.pack(fill=tk.BOTH, expand=True)

        # Frame für Listbox mit beiden Scrollbars
        output_listbox_frame = ttk.Frame(output_file_frame)
        output_listbox_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self.output_file_listbox = tk.Listbox(output_listbox_frame)

        # Vertikale Scrollbar
        output_file_v_scrollbar = ttk.Scrollbar(
            output_listbox_frame, orient="vertical", command=self.output_file_listbox.yview
        )
        self.output_file_listbox.configure(yscrollcommand=output_file_v_scrollbar.set)

        # Horizontale Scrollbar
        output_file_h_scrollbar = ttk.Scrollbar(
            output_listbox_frame, orient="horizontal", command=self.output_file_listbox.xview
        )
        self.output_file_listbox.configure(xscrollcommand=output_file_h_scrollbar.set)

        # Grid layout für Listbox und Scrollbars
        self.output_file_listbox.grid(row=0, column=0, sticky="nsew")
        output_file_v_scrollbar.grid(row=0, column=1, sticky="ns")
        output_file_h_scrollbar.grid(row=1, column=0, sticky="ew")

        output_listbox_frame.grid_rowconfigure(0, weight=1)
        output_listbox_frame.grid_columnconfigure(0, weight=1)

        self.output_file_listbox.bind(
            "<Double-Button-1>", lambda event: self._open_selected_file(event, self.output_files)
        )
        self.output_file_listbox.bind(
            "<<ListboxSelect>>", lambda event: self._on_file_selection(event, self.output_files)
        )

        # Middle top section: Buttons and Metadata mit horizontalem PanedWindow
        middle_top_paned = ttk.PanedWindow(middle_top_frame, orient=tk.HORIZONTAL)
        middle_top_paned.pack(fill=tk.BOTH, expand=True)

        # Buttons Frame (feste Breite)
        button_frame = ttk.Frame(middle_top_paned)
        button_frame.configure(width=200)  # Feste Breite für Buttons
        middle_top_paned.add(button_frame, weight=0)

        open_button = ttk.Button(button_frame, text="Open Files", command=self._open_files)
        open_button.pack(pady=8, fill=tk.X)

        remove_selected_button = ttk.Button(
            button_frame, text="Remove Selected", command=self._remove_selected_input_files
        )
        remove_selected_button.pack(pady=1, fill=tk.X)

        self.run_buttons = {}
        for mode, label in self.processing_modes:
            button = ttk.Button(
                button_frame, text=label, command=partial(self._run_processing, mode=mode)
            )
            button.pack(pady=1, fill=tk.X)
            self.run_buttons[mode] = button

        self.clear_input_button = ttk.Button(
            button_frame, text="Clear Input Files", command=self._clear_input_files
        )
        self.clear_input_button.pack(pady=8, fill=tk.X)

        self.clear_output_button = ttk.Button(
            button_frame, text="Clear Generated Files", command=self._clear_output_files
        )
        self.clear_output_button.pack(pady=1, fill=tk.X)

        self.progress = ttk.Progressbar(button_frame, mode="indeterminate")
        self.progress.pack(pady=0, fill=tk.X)

        # Metadata Display Frame (expandierbar)
        metadata_frame = ttk.LabelFrame(middle_top_paned, text="File Metadata")
        middle_top_paned.add(metadata_frame, weight=1)

        # Frame für Text widget mit beiden Scrollbars
        metadata_text_frame = ttk.Frame(metadata_frame)
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

        # Matplotlib Plot Frame
        plot_frame.grid_rowconfigure(0, weight=1)  # Canvas
        plot_frame.grid_rowconfigure(1, weight=0)  # Toolbar
        plot_frame.grid_columnconfigure(0, weight=1)

        # Setup Matplotlib figure and canvas
        self.fig, self.ax = plt.subplots(figsize=(8, 4))  # Kleinere initiale Höhe
        self.fig.set_facecolor("#EEEEEE")  # Light grey background for the figure
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=0, column=0, sticky="nsew")

        # Add Matplotlib toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, plot_frame, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.grid(row=1, column=0, sticky="ew")  # Position toolbar below canvas
        self.canvas_widget.config(cursor="hand2")  # Change cursor when hovering over plot

        self.ax.set_facecolor("#EEEEEE")  # Light grey background for the axes
        self.ax.tick_params(
            left=False, right=False, labelleft=False, labelbottom=False, bottom=False
        )  # Hide axis labels and ticks

        # Log output Frame
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
        log_controls.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 0))

        ttk.Button(log_controls, text="Clear Log", command=self._clear_log).pack(side=tk.LEFT)

        ttk.Label(log_controls, text="Log Level:").pack(side=tk.LEFT, padx=(0, 0))
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
        for mode, label in self.processing_modes:
            file_menu.add_command(label=label, command=partial(self._run_processing, mode=mode))

        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)

        # Options menu
        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=options_menu)
        options_menu.add_command(label="Settings", command=self._open_settings)

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

    def _clear_input_files(self):
        """Clear the input file list."""
        self.input_files.clear()
        self.input_file_listbox.delete(0, tk.END)
        self.logger.info("Input file list cleared")
        self._clear_metadata_and_plot()  # Clear plot and metadata when input files are cleared

    def _clear_output_files(self):
        """Clear the output file list."""
        self.output_files.clear()
        self.output_file_listbox.delete(0, tk.END)
        self.logger.info("Generated file list cleared")
        self._clear_metadata_and_plot()  # Clear plot and metadata when output files are cleared

    def _remove_selected_input_files(self):
        """Remove selected files from the input file list."""
        selected_indices = self.input_file_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "No files selected to remove!")
            return

        # Delete from listbox from end to start to avoid index issues
        for i in reversed(selected_indices):
            # If the removed file was the one currently displayed, clear metadata/plot
            if self.input_files[i]["path"] == self._last_selected_file_path:
                self._clear_metadata_and_plot()
            self.input_file_listbox.delete(i)
            del self.input_files[i]
        self.logger.info(f"Removed {len(selected_indices)} selected input files.")

    def _on_file_selection(self, event, file_list_source):
        """Handle selection change in file listboxes to update metadata/plot."""
        selected_indices = event.widget.curselection()
        if selected_indices:
            index = selected_indices[0]  # Get the first selected item
            file_path_str = file_list_source[index]["path"]
            self._parse_and_display_file(Path(file_path_str))
        else:
            self._clear_metadata_and_plot()

    def _open_selected_file(self, event, file_list_source):
        """Opens the selected file in the system's default application or explorer.
        Also triggers parsing and display for the selected file."""
        selection_index = event.widget.nearest(event.y)
        if selection_index == -1:  # No item clicked
            return

        file_path_str = file_list_source[selection_index]["path"]
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
            self.logger.info(f"Opened file: {file_path}")
        except Exception as e:
            self.logger.error(f"Could not open file {file_path}: {e}")
            messagebox.showerror("Error", f"Could not open file {file_path}: {e}")

        # After opening, also parse and display it in the GUI
        self._parse_and_display_file(file_path)

    def _open_files(self):
        """Open file dialog and add files to list."""
        files = filedialog.askopenfilenames(
            title="Select input files",
            filetypes=[
                ("GPX/KML files", "*.gpx *.kml *.zip"),  # Added KML support
                ("GPX files", "*.gpx"),
                ("KML files", "*.kml"),
                ("ZIP files", "*.zip"),
                ("All files", "*.*"),
            ],
        )

        new_files = 0
        for file_path_str in files:
            file_path = Path(file_path_str)
            if file_path_str not in [f["path"] for f in self.input_files]:
                try:
                    file_size_kb = file_path.stat().st_size / 1024
                    self.input_files.append({"path": file_path_str, "size": file_size_kb})
                    self.input_file_listbox.insert(
                        tk.END, f"{file_path.name} ({file_size_kb:.2f} KB)"
                    )
                    new_files += 1
                except Exception as e:
                    self.logger.warning(f"Could not get size for {file_path_str}: {e}")
                    self.input_files.append({"path": file_path_str, "size": 0})
                    self.input_file_listbox.insert(tk.END, f"{file_path.name} (N/A KB)")

        if new_files > 0:
            self.logger.info(f"Added {new_files} new files to processing list")
        else:
            self.logger.debug("No new files selected")

    def _update_output_listbox(self, generated_files_info):
        """Updates the output file listbox with newly generated files."""
        self.output_file_listbox.delete(0, tk.END)  # Clear current list
        self.output_files.clear()  # Clear internal list
        for file_path_str in generated_files_info:
            file_path = Path(file_path_str)
            try:
                file_size_kb = file_path.stat().st_size / 1024
                self.output_files.append({"path": file_path_str, "size": file_size_kb})
                self.output_file_listbox.insert(tk.END, f"{file_path.name} ({file_size_kb:.2f} KB)")
            except Exception as e:
                self.logger.warning(f"Could not get size for generated file {file_path_str}: {e}")
                self.output_files.append({"path": file_path_str, "size": 0})
                self.output_file_listbox.insert(tk.END, f"{file_path.name} (N/A KB)")

        if generated_files_info:
            output_dir = Path(generated_files_info[0]).parent
            self.logger.info(f"Generated files saved in: {output_dir}")  # Log directory

    def _run_processing(self, mode="compress_files"):
        """Run the processing in a separate thread."""
        selected_indices = self.input_file_listbox.curselection()
        files_to_process = []

        if selected_indices:
            for i in selected_indices:
                files_to_process.append(self.input_files[i]["path"])
        else:
            files_to_process = [f["path"] for f in self.input_files]

        if not files_to_process:
            self.logger.warning("No input files selected or all are deselected.")
            messagebox.showwarning("Warning", "No input files selected or all are deselected!")
            return

        self.logger.info(f"Starting processing of {len(files_to_process)} files in mode: {mode}")

        # Disable all buttons during processing
        for button in self.run_buttons.values():
            button.config(state="disabled")
        self.clear_input_button.config(state="disabled")
        self.clear_output_button.config(state="disabled")
        self.progress.start()

        # Run in separate thread to avoid blocking GUI
        thread = threading.Thread(
            target=self._process_files,
            args=(
                mode,
                files_to_process,
            ),
            daemon=True,
        )
        thread.start()

    def _process_files(self, mode="compress_files", files_to_process=None):
        """Process the selected files."""
        generated_files_paths = []
        try:
            self.logger.info("=== Processing Started ===")
            self.logger.info("Processing files...")

            if files_to_process is None:
                files_to_process = []  # Should not happen with the check in _run_processing

            # Create and run project
            project = BaseGPXProcessor(
                files_to_process,  # Pass selected files
                self.config_manager.get_category("cli").output.default,
                self.config_manager.get_category("cli").min_dist.default,
                self.config_manager.get_category("app").date_format.default,
                self.config_manager.get_category("cli").elevation.default,
                self.logger,
            )
            # implement switch case for different processing modes
            if mode == "compress_files":
                generated_files_paths = project.compress_files()
            elif mode == "merge_files":
                generated_files_paths = project.merge_files()
            elif mode == "extract_pois":
                generated_files_paths = project.extract_pois()
            else:
                self.logger.warning(f"Unknown mode: {mode}")

            self.logger.info(f"Completed: {len(files_to_process)} files processed")
            self.logger.info("=== All files processed successfully! ===")

            self.root.after(0, self._update_output_listbox, generated_files_paths)

        except Exception as err:
            self.logger.error(f"Processing failed: {err}", exc_info=True)
            # Show error dialog in main thread
            self.root.after(
                0, lambda e=err: messagebox.showerror("Error", f"Processing failed: {e}")
            )

        finally:
            # Re-enable controls in main thread
            self.root.after(0, self._processing_finished)

    def _processing_finished(self):
        """Re-enable controls after processing is finished."""
        for button in self.run_buttons.values():
            button.config(state="normal")
        self.clear_input_button.config(state="normal")
        self.clear_output_button.config(state="normal")
        self.progress.stop()

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
        """Open help documentation in browser."""
        self.logger.debug("Opening help documentation")
        webbrowser.open("https://gpx-kml-converter.readthedocs.io/en/stable/")

    def _show_about(self):
        """Show about dialog."""
        self.logger.debug("Showing about dialog")
        messagebox.showinfo("About", "gpx-kml-converter\n\nCopyright by Paul")

    def _on_closing(self):
        """Handle application closing."""
        self.logger.info("Closing GUI application")
        disconnect_gui_logging()
        self.root.quit()
        self.root.destroy()

    def _clear_metadata_and_plot(self):
        """Clears the metadata text and the matplotlib plot."""
        self.metadata_text.config(state=tk.NORMAL)
        self.metadata_text.delete(1.0, tk.END)
        self.metadata_text.config(state=tk.DISABLED)

        self.ax.clear()
        self.ax.set_facecolor("#EEEEEE")  # Reset background
        self.ax.tick_params(
            left=False, right=False, labelleft=False, labelbottom=False, bottom=False
        )  # Hide axis labels and ticks
        self.canvas.draw()
        self._last_selected_file_path = None
        self.logger.debug("Cleared metadata display and plot.")

    def _parse_and_display_file(self, file_path: Path):
        """Parses a GPX/KML file and updates the metadata display and plot."""
        if not GEOPANDAS_AVAILABLE:
            self.logger.warning("Geopandas is not available. Cannot display map visualization.")
            self.metadata_text.config(state=tk.NORMAL)
            self.metadata_text.delete(1.0, tk.END)
            self.metadata_text.insert(
                tk.END,
                "Geopandas library not found. Map visualization is disabled.\n"
                "Please install it (e.g., pip install geopandas matplotlib).",
            )
            self.metadata_text.config(state=tk.DISABLED)
            return

        if not file_path or not file_path.exists():
            self.logger.warning(f"File does not exist or is not specified: {file_path}")
            self._clear_metadata_and_plot()
            return

        if self._last_selected_file_path == file_path:
            self.logger.debug(f"File {file_path.name} is already displayed.")
            return

        self.logger.info(f"Parsing and displaying file: {file_path.name}")
        self._last_selected_file_path = file_path

        # Clear previous data
        self._clear_metadata_and_plot()

        # Use BaseGPXProcessor to load the file
        try:
            temp_processor = BaseGPXProcessor(
                input_=str(file_path),
                logger=self.logger,
                output=None,
                min_dist=0,
                date_format="%Y-%m-%d",
                elevation=True,  # Set elevation to True to get stats
            )
            gpx_data = None
            if file_path.suffix.lower() == ".gpx":
                gpx_data = temp_processor._load_gpx_file(file_path)
            elif file_path.suffix.lower() == ".kml":
                gpx_data = temp_processor._load_kml_file(file_path)
            else:
                self.logger.warning(f"Unsupported file type for visualization: {file_path.suffix}")
                self.metadata_text.config(state=tk.NORMAL)
                self.metadata_text.insert(
                    tk.END, f"Unsupported file type for visualization: {file_path.suffix}"
                )
                self.metadata_text.config(state=tk.DISABLED)
                return

            if gpx_data:
                self._update_metadata_display(gpx_data, file_path.name)
                self._plot_gpx_data(gpx_data)
            else:
                self.logger.error(f"Failed to load GPX/KML data from {file_path.name}")
                self.metadata_text.config(state=tk.NORMAL)
                self.metadata_text.insert(
                    tk.END,
                    f"Failed to load GPX/KML data from {file_path.name}.\nCheck log for details.",
                )
                self.metadata_text.config(state=tk.DISABLED)

        except Exception as e:
            self.logger.error(f"Error parsing file {file_path.name}: {e}", exc_info=True)
            self._clear_metadata_and_plot()
            self.metadata_text.config(state=tk.NORMAL)
            self.metadata_text.insert(
                tk.END,
                f"Error processing file {file_path.name}:\n{e}\nCheck log for full traceback.",
            )
            self.metadata_text.config(state=tk.DISABLED)

    def _update_metadata_display(self, gpx_data: gpxpy.gpx.GPX, file_name: str):
        """Updates the metadata text widget with information from the GPX data."""
        self.metadata_text.config(state=tk.NORMAL)  # Enable editing
        self.metadata_text.delete(1.0, tk.END)

        self.metadata_text.insert(tk.END, f"File: {file_name}\n")
        self.metadata_text.insert(tk.END, "-------------------------------------\n")

        num_tracks = len(gpx_data.tracks)
        num_routes = len(gpx_data.routes)
        num_waypoints = len(gpx_data.waypoints)

        self.metadata_text.insert(tk.END, f"Tracks: {num_tracks}\n")
        self.metadata_text.insert(tk.END, f"Routes: {num_routes}\n")
        self.metadata_text.insert(tk.END, f"Waypoints: {num_waypoints}\n")
        self.metadata_text.insert(tk.END, "\n")

        # Display Tracks
        if num_tracks > 0:
            self.metadata_text.insert(tk.END, "Tracks:\n")
            for i, track in enumerate(gpx_data.tracks):
                track_name = track.name if track.name else f"Unnamed Track {i + 1}"
                distance_2d = track.length_2d() if track.length_2d() is not None else 0

                # Calculate uphill/downhill if elevation data is present
                uphill, downhill = 0, 0
                if track.segments:
                    # gpxpy has built-in functions for this if elevation is present
                    try:
                        up_down = track.get_uphill_downhill()
                        uphill = up_down.uphill
                        downhill = up_down.downhill
                    except Exception as e:
                        self.logger.debug(
                            f"Could not calculate uphill/downhill for track {track_name}: {e}"
                        )

                self.metadata_text.insert(tk.END, f"  - {track_name}: {distance_2d / 1000:.2f} km")
                if uphill is not None and downhill is not None:
                    self.metadata_text.insert(tk.END, f" (↑{uphill:.1f}m ↓{downhill:.1f}m)\n")
                else:
                    self.metadata_text.insert(tk.END, "\n")
            self.metadata_text.insert(tk.END, "\n")

        # Display Routes
        if num_routes > 0:
            self.metadata_text.insert(tk.END, "Routes:\n")
            for i, route in enumerate(gpx_data.routes):
                route_name = route.name if route.name else f"Unnamed Route {i + 1}"
                distance_2d = route.length_2d() if route.length_2d() is not None else 0

                # Calculate uphill/downhill for routes
                uphill, downhill = 0, 0
                # gpxpy does not directly provide get_uphill_downhill for routes,
                # so we can manually iterate or if it's treated like a track internally
                # For now, let's keep it simple or implement manual calculation if needed.
                # Assuming BaseGPXProcessor would handle elevation adjustments on points.
                if route.points:
                    try:
                        # Temporary track for elevation calculation
                        temp_track = gpxpy.gpx.GPXTrack()
                        temp_segment = gpxpy.gpx.GPXTrackSegment()
                        temp_segment.points.extend(route.points)
                        temp_track.segments.append(temp_segment)
                        up_down = temp_track.get_uphill_downhill()
                        uphill = up_down.uphill
                        downhill = up_down.downhill
                    except Exception as e:
                        self.logger.debug(
                            f"Could not calculate uphill/downhill for route {route_name}: {e}"
                        )

                self.metadata_text.insert(tk.END, f"  - {route_name}: {distance_2d / 1000:.2f} km")
                if uphill is not None and downhill is not None:
                    self.metadata_text.insert(tk.END, f" (↑{uphill:.1f}m ↓{downhill:.1f}m)\n")
                else:
                    self.metadata_text.insert(tk.END, "\n")
            self.metadata_text.insert(tk.END, "\n")

        self.metadata_text.config(state=tk.DISABLED)  # Disable editing

    def _plot_gpx_data(self, gpx_data: gpxpy.gpx.GPX):
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
        if all_points_coords:
            all_lons = [coord[0] for coord in all_points_coords]
            all_lats = [coord[1] for coord in all_points_coords]

            min_lat = min(all_lats)
            max_lat = max(all_lats)
            min_lon = min(all_lons)
            max_lon = max(all_lons)

            # Add a small buffer around the points for better visualization
            lat_buffer = (max_lat - min_lat) * 0.1 if (max_lat - min_lat) > 0 else 0.1
            lon_buffer = (max_lon - min_lon) * 0.1 if (max_lon - min_lon) > 0 else 0.1

            self.ax.set_xlim(min_lon - lon_buffer, max_lon + lon_buffer)
            self.ax.set_ylim(min_lat - lat_buffer, max_lat + lat_buffer)
        else:
            # Default view if no data is plotted (e.g., world map or Europe)
            self.ax.set_xlim(-10, 30)  # Default to a Europe-ish view
            self.ax.set_ylim(35, 65)

        self.ax.set_aspect("equal", adjustable="box")  # Maintain aspect ratio
        self.ax.tick_params(
            left=False, right=False, labelleft=False, labelbottom=False, bottom=False
        )  # Hide axis labels and ticks
        self.canvas.draw()  # Redraw the canvas


def main():
    """Main entry point for the GUI application."""
    root = tk.Tk()
    try:
        MainGui(root)
        root.mainloop()
    except Exception as e:
        print(f"GUI startup failed: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
