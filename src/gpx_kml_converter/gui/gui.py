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
from tkinter import filedialog, font, messagebox, ttk

# Matplotlib imports for plotting
import matplotlib.pyplot as plt
import ttkbootstrap
from config_cli_gui.gui import SettingsDialogGenerator, ToolTip
from config_cli_gui.persistence import read_last_used_config
from gpxpy.gpx import GPX
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from gpx_kml_converter.application.processing import process_gpx_files
from gpx_kml_converter.config.config import ConfigParameterManager
from gpx_kml_converter.core.file_loader import FileOrigin, GeoFileManager
from gpx_kml_converter.core.gpx_plotter import GPXPlotter
from gpx_kml_converter.core.logging import (
    connect_gui_logging,
    disconnect_gui_logging,
    get_logger,
    initialize_logging,
)
from gpx_kml_converter.gui.artifacts import (
    ArtifactGroupIdentity,
    ArtifactIdentity,
    FileCollection,
    FileSummary,
    artifact_groups,
    artifact_label,
    artifact_metadata,
    plot_reference,
    remove_artifacts,
    selected_input_paths,
    summarize_gpx,
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


class TextNavigationToolbar(NavigationToolbar2Tk):
    """Matplotlib toolbar with text controls instead of platform-dependent icons."""

    toolitems = tuple(
        (text, tooltip, None, callback)
        for text, tooltip, _image_file, callback in NavigationToolbar2Tk.toolitems
    )

    def _Button(self, text, image_file, toggle, command):
        if toggle:
            variable = tk.IntVar(master=self)
            button = tk.Checkbutton(
                master=self,
                text=text,
                command=command,
                indicatoron=False,
                variable=variable,
                offrelief="flat",
                overrelief="groove",
                borderwidth=1,
            )
            button.var = variable
        else:
            button = tk.Button(
                master=self,
                text=text,
                command=command,
                relief="flat",
                overrelief="groove",
                borderwidth=1,
            )
        button.pack(side=tk.LEFT)
        return button


class MainGui:
    """Main GUI application class."""

    processing_modes = [
        ("compress", "Process Files"),
        ("merge", "Merge Files"),
        ("extract-pois", "Extract POIs from Tracks"),
    ]

    def __init__(self, root):
        self.root = root
        self.root.title("gpx-kml-converter")
        self.root.geometry("1400x800")  # Increased width and height for new layout

        # Initialize configuration
        self.config_manager = ConfigParameterManager("config.yaml")

        # Initialize logging system
        self.logger_manager = initialize_logging(self.config_manager)
        self.logger = get_logger("gui.main")

        # File lists - now hold Path to GPX object mapping
        self.gpx_input: dict[Path, GPX] = {}
        self.gpx_output: dict[Path, GPX] = {}
        self._tree_identity: dict[str, ArtifactIdentity] = {}
        self._tree_group_identity: dict[str, ArtifactGroupIdentity] = {}
        self._identity_tree_item: dict[ArtifactIdentity, str] = {}
        self._file_summaries: dict[tuple[FileCollection, Path], FileSummary] = {}
        self._file_origins: dict[tuple[FileCollection, Path], FileOrigin] = {}
        self._file_labels: dict[tuple[FileCollection, Path], str] = {}
        self._virtual_files: set[tuple[FileCollection, Path]] = set()
        self._tree_item_counter = 0
        self._working_copy_counter = 0
        self._active_identity: ArtifactIdentity | None = None
        self._active_profile_identity: ArtifactIdentity | None = None
        self.batch_status_var = tk.StringVar(master=self.root)

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
        self._rebuild_artifact_tree()
        self._show_empty_inspector("Open files to browse tracks, routes, and POIs.")

    def _build_widgets(self):
        """Build the main GUI widgets."""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        main_horizontal_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        main_horizontal_paned.pack(fill=tk.BOTH, expand=True)

        workspace_frame = ttk.LabelFrame(main_horizontal_paned, text="Workspace")
        center_vertical_paned = ttk.PanedWindow(main_horizontal_paned, orient=tk.VERTICAL)
        map_frame = ttk.LabelFrame(main_horizontal_paned, text="Map")
        main_horizontal_paned.add(workspace_frame, weight=2)
        main_horizontal_paned.add(center_vertical_paned, weight=2)
        main_horizontal_paned.add(map_frame, weight=5)

        metadata_frame = ttk.LabelFrame(center_vertical_paned, text="Inspector")
        profile_plot_frame = ttk.LabelFrame(center_vertical_paned, text="Elevation Profile")
        center_vertical_paned.add(metadata_frame, weight=2)
        center_vertical_paned.add(profile_plot_frame, weight=1)

        self._build_workspace_browser(workspace_frame)
        self._build_metadata_display(metadata_frame)
        self._build_plot_display(map_frame)
        self._build_profile_plot(profile_plot_frame)

    def _build_workspace_browser(self, parent_frame):
        controls = ttk.Frame(parent_frame)
        controls.pack(fill=tk.X, padx=4, pady=4)
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)
        ttk.Button(controls, text="Open Files", command=self._open_files).grid(
            row=0, column=0, sticky="ew"
        )
        ttk.Button(controls, text="Select All Inputs", command=self._select_all_input_files).grid(
            row=0, column=1, sticky="ew", padx=(4, 0)
        )
        ttk.Button(
            controls,
            text="Use Selected Results as Inputs",
            command=self._use_selected_outputs_as_inputs,
        ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        tree_frame = ttk.Frame(parent_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        self.artifact_tree = ttk.Treeview(
            tree_frame, selectmode="extended", show="tree", takefocus=True
        )
        vertical_scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.artifact_tree.yview
        )
        horizontal_scrollbar = ttk.Scrollbar(
            tree_frame, orient="horizontal", command=self.artifact_tree.xview
        )
        self.artifact_tree.configure(
            yscrollcommand=vertical_scrollbar.set,
            xscrollcommand=horizontal_scrollbar.set,
        )
        self.artifact_tree.grid(row=0, column=0, sticky="nsew")
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        self.artifact_tree.bind("<<TreeviewSelect>>", self._on_browser_selection)
        self.artifact_tree.bind("<Double-Button-1>", self._open_selected_tree_file)
        self.artifact_tree.bind("<Button-3>", self._show_browser_context_menu)
        self.artifact_tree.bind("<Shift-F10>", self._show_keyboard_context_menu)
        self.artifact_tree.bind("<Menu>", self._show_keyboard_context_menu)
        self.artifact_tree.bind("<Delete>", self._delete_selected_workspace_items)
        self.artifact_tree.bind("<KP_Delete>", self._delete_selected_workspace_items)
        if sys.platform == "darwin":
            self.artifact_tree.bind("<Button-2>", self._show_browser_context_menu)
            self.artifact_tree.bind("<Control-Button-1>", self._show_browser_context_menu)

        self.batch_status_label = ttk.Label(
            parent_frame, textvariable=self.batch_status_var, anchor=tk.W
        )
        self.batch_status_label.pack(fill=tk.X, padx=4, pady=(0, 4))
        self._build_processing_controls(parent_frame)

    def _build_processing_controls(self, parent_frame):
        """Build processing actions below the artifact tree."""

        self.run_buttons = {}
        for mode, label in self.processing_modes:
            button = ttk.Button(
                parent_frame,
                text=label,
                command=partial(self._run_processing, mode=mode),
            )
            button.pack(pady=1, padx=4, fill=tk.X)
            ToolTip(button, label)
            self.run_buttons[mode] = button

        self.clear_files_button = ttk.Button(
            parent_frame, text="Clear Workspace", command=self._clear_files
        )
        ToolTip(self.clear_files_button, "Clear all input and generated files")
        self.clear_files_button.pack(pady=4, padx=4, fill=tk.X)

        self.progress = ttk.Progressbar(parent_frame, mode="indeterminate")
        self.progress.pack(pady=(0, 4), padx=4, fill=tk.X)

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
        self.toolbar = TextNavigationToolbar(self.canvas, parent_frame, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.grid(row=1, column=0, sticky="ew")  # Position toolbar below canvas
        self.canvas_widget.config(cursor="hand2")  # Change cursor when hovering over plot

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
            self.log_window.withdraw()

    def _build_log_window(self):
        """Build the log window as a separate window."""
        if self.log_window is not None:
            self.log_window.deiconify()
            self.log_window.lift()
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
        self.log_level_var = tk.StringVar(value=self.config_manager.app.log_level.value)
        log_level_combo = ttk.Combobox(
            log_controls,
            textvariable=self.log_level_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            state="readonly",
            width=10,
        )
        log_level_combo.pack(side=tk.LEFT)
        log_level_combo.bind("<<ComboboxSelected>>", self._on_log_level_changed)
        self.log_window.withdraw()

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
        """Clear all files from the workspace."""
        self.gpx_input.clear()
        self.gpx_output.clear()
        self._file_summaries.clear()
        self._file_origins.clear()
        self._file_labels.clear()
        self._virtual_files.clear()
        self._rebuild_artifact_tree()
        self._show_empty_inspector()
        self.logger.info("Workspace cleared")

    def _select_all_input_files(self):
        """Select every loaded input so batch processing is explicit and quick."""
        item_ids = [
            self._identity_tree_item[ArtifactIdentity("input", path, "file")]
            for path in self.gpx_input
        ]
        self.artifact_tree.selection_set(*item_ids)
        if item_ids:
            self.artifact_tree.focus(item_ids[-1])
            self.artifact_tree.see(item_ids[-1])
        self._on_browser_selection()

    @staticmethod
    def _selected_paths(file_map: dict[Path, GPX], selected_indices: tuple[int, ...]) -> list[Path]:
        """Resolve selected positions to paths; an empty selection means all files."""
        paths = list(file_map)
        if not selected_indices:
            return paths
        return [paths[index] for index in selected_indices if 0 <= index < len(paths)]

    @staticmethod
    def _add_results_to_inputs(
        input_files: dict[Path, GPX], output_files: dict[Path, GPX], selected_paths: list[Path]
    ) -> list[Path]:
        """Add selected results once and return paths that were newly added."""
        added_paths = []
        for path in selected_paths:
            if path not in input_files:
                input_files[path] = output_files[path]
                added_paths.append(path)
        return added_paths

    def _use_selected_outputs_as_inputs(self):
        """Add selected generated files to the input workspace for another processing step."""
        selected_paths = self._selected_tree_file_paths("output")
        if not selected_paths:
            messagebox.showwarning("Warning", "Select at least one generated result first.")
            return

        added_paths = self._add_results_to_inputs(self.gpx_input, self.gpx_output, selected_paths)
        for path in added_paths:
            output_key = ("output", path)
            input_key = ("input", path)
            if output_key in self._file_origins:
                self._file_origins[input_key] = self._file_origins[output_key]
            if output_key in self._file_labels:
                self._file_labels[input_key] = self._file_labels[output_key]
            if output_key in self._virtual_files:
                self._virtual_files.add(input_key)
        self._rebuild_artifact_tree()
        input_items = [
            self._identity_tree_item[ArtifactIdentity("input", path, "file")]
            for path in (added_paths or selected_paths)
            if path in self.gpx_input
        ]
        self.artifact_tree.selection_set(*input_items)
        if input_items:
            self.artifact_tree.focus(input_items[0])
            self.artifact_tree.see(input_items[0])
        self._on_browser_selection()
        self.logger.info(f"Added {len(added_paths)} generated result(s) to the input workspace.")

    def _new_tree_item_id(self) -> str:
        self._tree_item_counter += 1
        return f"artifact-{self._tree_item_counter}"

    def _rebuild_artifact_tree(self):
        """Refresh browser rows after workspace contents change, not on selection."""
        self.artifact_tree.delete(*self.artifact_tree.get_children(""))
        self._tree_identity.clear()
        self._tree_group_identity.clear()
        self._identity_tree_item.clear()
        roots = {
            "input": self.artifact_tree.insert(
                "", tk.END, iid="workspace-inputs", text=f"Inputs ({len(self.gpx_input)})"
            ),
            "output": self.artifact_tree.insert(
                "", tk.END, iid="workspace-generated", text=f"Generated ({len(self.gpx_output)})"
            ),
        }
        self.artifact_tree.item(roots["input"], open=True)
        self.artifact_tree.item(roots["output"], open=True)

        for collection, file_map in (("input", self.gpx_input), ("output", self.gpx_output)):
            if not file_map:
                self.artifact_tree.insert(
                    roots[collection],
                    tk.END,
                    iid=f"empty-{collection}",
                    text="No files loaded",
                )
            for file_path, gpx in file_map.items():
                cache_key = (collection, file_path)
                if cache_key not in self._file_summaries:
                    self._file_summaries[cache_key] = summarize_gpx(gpx)
                summary = self._file_summaries[cache_key]
                file_identity = ArtifactIdentity(collection, file_path, "file")
                display_name = self._file_labels.get(cache_key)
                if display_name is None:
                    origin = self._file_origins.get(cache_key)
                    display_name = origin.display_name if origin is not None else file_path.name
                file_item = self._insert_artifact(
                    roots[collection],
                    file_identity,
                    f"{display_name} ({summary.artifact_count})",
                )
                for group_label, identities in artifact_groups(gpx, collection, file_path):
                    group_item = self.artifact_tree.insert(
                        file_item,
                        tk.END,
                        iid=self._new_tree_item_id(),
                        text=f"{group_label} ({len(identities)})",
                    )
                    self._tree_group_identity[group_item] = ArtifactGroupIdentity(
                        collection, file_path, identities[0].kind
                    )
                    for identity in identities:
                        self._insert_artifact(
                            group_item,
                            identity,
                            artifact_label(gpx, identity),
                        )

        self._update_batch_status()

    def _insert_artifact(self, parent: str, identity: ArtifactIdentity, label: str) -> str:
        item_id = self._new_tree_item_id()
        self.artifact_tree.insert(parent, tk.END, iid=item_id, text=label)
        self._tree_identity[item_id] = identity
        self._identity_tree_item[identity] = item_id
        return item_id

    def _selected_tree_file_paths(self, collection: FileCollection) -> list[Path]:
        selected = {
            identity.file_path
            for item_id in self.artifact_tree.selection()
            if (identity := self._tree_identity.get(item_id)) is not None
            and identity.kind == "file"
            and identity.collection == collection
        }
        file_map = self.gpx_input if collection == "input" else self.gpx_output
        return [path for path in file_map if path in selected]

    def _selected_removal_kind(self) -> str | None:
        selected_kinds = set()
        for item_id in self.artifact_tree.selection():
            identity = self._tree_identity.get(item_id)
            group_identity = self._tree_group_identity.get(item_id)
            kind = (
                identity.kind
                if identity is not None
                else (group_identity.kind if group_identity is not None else None)
            )
            if kind is None:
                return None
            selected_kinds.add(kind)
        return next(iter(selected_kinds)) if len(selected_kinds) == 1 else None

    def _show_browser_context_menu(self, event):
        item_id = self.artifact_tree.identify_row(event.y)
        if item_id:
            self._show_browser_context_menu_at(item_id, event.x_root, event.y_root)
        return "break"

    def _show_keyboard_context_menu(self, _event=None):
        item_id = self.artifact_tree.focus()
        if not item_id:
            return "break"
        bounds = self.artifact_tree.bbox(item_id)
        if bounds:
            x, y, _width, height = bounds
            self._show_browser_context_menu_at(
                item_id,
                self.artifact_tree.winfo_rootx() + x,
                self.artifact_tree.winfo_rooty() + y + height,
            )
        return "break"

    def _show_browser_context_menu_at(self, item_id: str, x: int, y: int):
        if item_id not in self.artifact_tree.selection():
            self.artifact_tree.selection_set(item_id)
        self.artifact_tree.focus(item_id)
        menu = tk.Menu(self.root, tearoff=0)
        if item_id in self._tree_identity or item_id in self._tree_group_identity:
            menu.add_command(
                label="Open Containing Folder",
                command=lambda: self._open_containing_folder(item_id),
            )
            menu.add_separator()

        kind = self._selected_removal_kind()
        if kind == "file":
            menu.add_command(
                label="Remove from Workspace",
                command=self._delete_selected_workspace_items,
            )
        elif kind in {"track", "route", "waypoint"}:
            label = {"track": "Tracks", "route": "Routes", "waypoint": "POIs"}[kind]
            menu.add_command(
                label=f"Remove selected {label}",
                command=self._delete_selected_workspace_items,
            )
        else:
            menu.add_command(
                label="Remove unavailable for mixed selections",
                state=tk.DISABLED,
            )

        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _delete_selected_workspace_items(self, _event=None):
        kind = self._selected_removal_kind()
        if kind is None:
            messagebox.showwarning(
                "Cannot Remove Selection",
                "Select files or artifacts of one type before removing them.",
            )
            return "break"

        if kind == "file":
            selected_files = [
                self._tree_identity[item_id]
                for item_id in self.artifact_tree.selection()
                if item_id in self._tree_identity
            ]
            selected_paths = {identity.file_path for identity in selected_files}
            for file_path in selected_paths:
                for collection, file_map in (
                    ("input", self.gpx_input),
                    ("output", self.gpx_output),
                ):
                    file_map.pop(file_path, None)
                    cache_key = (collection, file_path)
                    self._file_summaries.pop(cache_key, None)
                    self._file_origins.pop(cache_key, None)
                    self._file_labels.pop(cache_key, None)
                    self._virtual_files.discard(cache_key)
            self.logger.info(f"Removed {len(selected_paths)} file(s) from the workspace.")
            self._rebuild_artifact_tree()
            self._show_empty_inspector()
            return "break"

        targets: dict[tuple[FileCollection, Path], set[int] | None] = {}
        for item_id in self.artifact_tree.selection():
            identity = self._tree_identity.get(item_id)
            group_identity = self._tree_group_identity.get(item_id)
            if group_identity is not None:
                targets[(group_identity.collection, group_identity.file_path)] = None
            elif identity is not None and identity.index is not None:
                target_key = (identity.collection, identity.file_path)
                if targets.get(target_key, set()) is not None:
                    targets.setdefault(target_key, set()).add(identity.index)

        new_paths = []
        for (collection, file_path), indexes in targets.items():
            file_map = self.gpx_input if collection == "input" else self.gpx_output
            source_gpx = file_map.get(file_path)
            if source_gpx is None:
                self.logger.error(f"GPX object not found for path: {file_path}")
                messagebox.showerror("Error", "The selected GPX data is no longer available.")
                return "break"

            derived_gpx = remove_artifacts(source_gpx, kind, indexes)
            origin = self._file_origins.get((collection, file_path), FileOrigin(file_path))
            self._working_copy_counter += 1
            working_copy_path = (
                origin.source_path.parent
                / f".{origin.source_path.name}.workspace"
                / f"working-copy-{self._working_copy_counter}-{origin.output_stem}.gpx"
            )
            output_key = ("output", working_copy_path)
            self.gpx_output[working_copy_path] = derived_gpx
            self._file_origins[output_key] = origin
            self._file_labels[output_key] = (
                f"{origin.output_stem} (Working Copy {self._working_copy_counter}).gpx"
            )
            self._virtual_files.add(output_key)
            self._file_summaries.pop(output_key, None)
            new_paths.append(working_copy_path)

        self._rebuild_artifact_tree()
        result_items = [
            self._identity_tree_item[ArtifactIdentity("output", path, "file")] for path in new_paths
        ]
        if result_items:
            self.artifact_tree.selection_set(*result_items)
            self.artifact_tree.focus(result_items[-1])
            self.artifact_tree.see(result_items[-1])
            self._on_browser_selection()
        self.logger.info(
            f"Created {len(new_paths)} derived working copy/copies with selected {kind}s removed."
        )
        return "break"

    def _selected_input_paths(self) -> list[Path]:
        selected_identities = [
            self._tree_identity[item_id]
            for item_id in self.artifact_tree.selection()
            if item_id in self._tree_identity
        ]
        return selected_input_paths(self.gpx_input, selected_identities)

    def _update_batch_status(self):
        selected_count = len(self._selected_tree_file_paths("input"))
        total_count = len(self.gpx_input)
        if selected_count:
            self.batch_status_var.set(f"Batch: {selected_count} of {total_count} input files")
        else:
            self.batch_status_var.set(
                f"Batch: all {total_count} input files (no input files selected)"
            )

    def _on_browser_selection(self, _event=None):
        self._update_batch_status()
        item_id = self.artifact_tree.focus()
        identity = self._tree_identity.get(item_id)
        group_identity = self._tree_group_identity.get(item_id)
        if identity is None and group_identity is not None:
            identity = ArtifactIdentity(group_identity.collection, group_identity.file_path, "file")
        if identity is None:
            parent_item = self.artifact_tree.parent(item_id)
            parent_identity = self._tree_identity.get(parent_item)
            if parent_identity is not None and parent_identity.kind == "file":
                identity = parent_identity
        if identity is None:
            if self._active_identity is not None:
                self._show_empty_inspector()
            return
        if identity == self._active_identity:
            return

        file_map = self.gpx_input if identity.collection == "input" else self.gpx_output
        gpx = file_map.get(identity.file_path)
        if gpx is None:
            self.logger.error(f"GPX object not found for path: {identity.file_path}")
            self._show_empty_inspector("The selected GPX data is no longer available.")
            return

        self._active_identity = identity
        self.metadata_text.config(state=tk.NORMAL)
        self.metadata_text.delete("1.0", tk.END)
        self.metadata_text.insert(
            tk.END,
            "\n".join(
                f"{label}: {value}"
                for label, value in artifact_metadata(
                    gpx,
                    identity,
                    self._file_summaries.get((identity.collection, identity.file_path)),
                    self._file_labels.get((identity.collection, identity.file_path)),
                )
            ),
        )
        self.metadata_text.config(state=tk.DISABLED)

        artifact_ref = plot_reference(identity)
        self.gpx_map_plotter.plot_gpx_map(gpx, artifact_ref)

        if identity.kind == "track":
            if identity.index is None:
                raise ValueError("Active track identity is missing its index.")
            self.gpx_profile_plotter.plot_track_profile(gpx, identity.index)
            self._active_profile_identity = identity
        else:
            self.gpx_profile_plotter.clear_profile()
            self._active_profile_identity = None

    def _show_empty_inspector(self, message="Select a file or artifact to inspect."):
        self._active_identity = None
        self.metadata_text.config(state=tk.NORMAL)
        self.metadata_text.delete("1.0", tk.END)
        self.metadata_text.insert(tk.END, message)
        self.metadata_text.config(state=tk.DISABLED)
        if self.gpx_map_plotter is not None:
            self.gpx_map_plotter.clear_plot()
        if self.gpx_profile_plotter is not None:
            self.gpx_profile_plotter.clear_profile()
        self._active_profile_identity = None

    def _open_selected_tree_file(self, event):
        item_id = self.artifact_tree.identify_row(event.y)
        identity = self._tree_identity.get(item_id)
        group_identity = self._tree_group_identity.get(item_id)
        if identity is None and group_identity is not None:
            identity = ArtifactIdentity(group_identity.collection, group_identity.file_path, "file")
        if identity is None:
            return
        cache_key = (identity.collection, identity.file_path)
        origin = self._file_origins.get(cache_key, FileOrigin(identity.file_path))
        file_path = origin.source_path

        if cache_key in self._virtual_files:
            self.logger.warning(
                f"Working copy is not saved; opening its unchanged source file: {file_path}"
            )

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

    def _open_containing_folder(self, item_id: str):
        identity = self._tree_identity.get(item_id)
        group_identity = self._tree_group_identity.get(item_id)
        if identity is None and group_identity is not None:
            identity = ArtifactIdentity(group_identity.collection, group_identity.file_path, "file")
        if identity is None:
            return

        origin = self._file_origins.get(
            (identity.collection, identity.file_path), FileOrigin(identity.file_path)
        )
        directory = origin.source_path.parent
        if not directory.is_dir():
            self.logger.error(f"Containing folder not found: {directory}")
            messagebox.showerror("Error", f"Containing folder not found: {directory}")
            return

        try:
            if sys.platform == "win32":
                os.startfile(directory)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", directory])
            else:
                subprocess.Popen(["xdg-open", directory])
            self.logger.info(f"Opened containing folder: {directory}")
        except OSError as error:
            self.logger.error(f"Could not open containing folder {directory}: {error}")
            messagebox.showerror("Error", f"Could not open containing folder: {error}")

    def _open_files(self):
        """Open files and add their parsed GPX objects to the workspace."""
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
        loaded_gpx_map = self.geo_file_manager.load_files_with_origins(file_paths_as_paths)

        if not loaded_gpx_map:
            self.logger.warning("No GPX data could be loaded from the selected files.")
            messagebox.showinfo("Info", "No GPX data could be loaded from the selected files.")
            return

        for path, loaded_file in loaded_gpx_map.items():
            if path not in self.gpx_input:
                self.gpx_input[path] = loaded_file.gpx
                cache_key = ("input", path)
                self._file_origins[cache_key] = loaded_file.origin
                self._file_labels[cache_key] = loaded_file.origin.display_name
                new_files_loaded += 1
            else:
                self.logger.info(f"File {path.name} already loaded. Skipping.")

        self.logger.info(f"Loaded {new_files_loaded} new GPX files.")
        if new_files_loaded > 0:
            self._rebuild_artifact_tree()
            self._select_all_input_files()

    def _run_processing(self, mode: str):
        """Run the selected processing mode in a separate thread."""
        selected_paths = self._selected_input_paths()
        if not selected_paths:
            messagebox.showwarning("Warning", "Load at least one input file to process.")
            return
        selected_gpx_objects = [self.gpx_input[path] for path in selected_paths]

        for button in self.run_buttons.values():
            button.config(state=tk.DISABLED)
        self.clear_files_button.config(state=tk.DISABLED)
        self.progress.start()
        self.logger.info(f"Starting '{mode}' processing for {len(selected_gpx_objects)} files...")

        def processing_thread():
            try:
                processed_gpx_map = process_gpx_files(
                    selected_gpx_objects,
                    mode=mode,
                    output=self.config_manager.cli.output.value,
                    tolerance=self.config_manager.cli.tolerance.value,
                    date_format=self.config_manager.app.date_format.value,
                    elevation=self.config_manager.cli.elevation.value,
                    logger=self.logger,
                    source_origins=[
                        self._file_origins.get(("input", path), FileOrigin(path))
                        for path in selected_paths
                    ],
                )

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
        """Publish generated files in the workspace tree."""
        self.gpx_output.update(processed_gpx_map)
        for path in processed_gpx_map:
            output_key = ("output", path)
            self._file_summaries.pop(output_key, None)
            self._file_origins[output_key] = FileOrigin(path)
            self._file_labels.pop(output_key, None)
            self._virtual_files.discard(output_key)
        self._rebuild_artifact_tree()
        if processed_gpx_map:
            last_path = next(reversed(processed_gpx_map))
            item_id = self._identity_tree_item[ArtifactIdentity("output", last_path, "file")]
            self.artifact_tree.selection_set(item_id)
            self.artifact_tree.focus(item_id)
            self.artifact_tree.see(item_id)
            self._on_browser_selection()

    def _reset_ui_state(self):
        """Reset UI elements after processing completes or fails."""
        self.progress.stop()
        for button in self.run_buttons.values():
            button.config(state=tk.NORMAL)
        self.clear_files_button.config(state=tk.NORMAL)

    def _clear_metadata_and_plot(self):
        """Clear the active inspector and its visualizations."""
        self._show_empty_inspector()

    def _open_settings(self):
        """Open the settings dialog."""
        self.logger.debug("Opening settings dialog")
        settings_dialog_generator = SettingsDialogGenerator(self.config_manager)
        dialog = settings_dialog_generator.create_settings_dialog(self.root)
        self.root.wait_window(dialog.dialog)

        if dialog.result == "ok":
            self.logger.info("Settings updated successfully")
            # Update log level selector if it changed
            self.log_level_var.set(self.config_manager.app.log_level.value)

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

    # Try to restore the last used configuration file so the GUI can start
    # with the user's preferred theme and settings.
    last = read_last_used_config(ConfigParameterManager.get_app_name())
    if last and Path(last).exists():
        _config = ConfigParameterManager(last)
    else:
        _config = ConfigParameterManager()

    theme_choice = _config.app.theme.value

    root: ttkbootstrap.Window = ttkbootstrap.Window(themename=theme_choice)

    font.nametofont("TkDefaultFont").configure(size=11)
    font.nametofont("TkTextFont").configure(size=11)
    font.nametofont("TkMenuFont").configure(size=11)
    font.nametofont("TkHeadingFont").configure(size=11)
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
