# Welcome to gpx-kml-converter

[![Github CI Status](https://github.com/pamagister/gpx-kml-converter/actions/workflows/main.yml/badge.svg)](https://github.com/pamagister/gpx-kml-converter/actions)
[![GitHub release](https://img.shields.io/github/v/release/pamagister/gpx-kml-converter)](https://github.com/pamagister/gpx-kml-converter/releases)
[![Read the Docs](https://readthedocs.org/projects/gpx-kml-converter/badge/?version=stable)](https://gpx-kml-converter.readthedocs.io/en/stable/)
[![License](https://img.shields.io/github/license/pamagister/gpx-kml-converter)](https://github.com/pamagister/gpx-kml-converter/blob/main/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/pamagister/gpx-kml-converter)](https://github.com/pamagister/gpx-kml-converter/issues)
[![PyPI](https://img.shields.io/pypi/v/gpx-kml-converter)](https://pypi.org/project/gpx-kml-converter/)

Welcome to the **GPX KML Converter** application, 
a versatile tool designed for processing geographical data files (GPX and KML). 
The application offers both an intuitive Graphical User Interface (GUI) and a robust 
command line interface for various file manipulation tasks.

## Installation

Download from [PyPI](https://pypi.org/).

💾 For more installation options see [install](https://gpx-kml-converter.readthedocs.io/en/stable/getting-started/install/).

```bash
pip install gpx-kml-converter
```

Run GUI from command line

```bash
gpx-kml-converter-gui
```

Run CLI from command line

```bash
gpx-kml-converter --help
```


## 2. Main Features 🚀

### 2.1. Graphical User Interface (GUI) 🖥️

The application features a comprehensive GUI that simplifies the process of managing and processing your geographical data.

* **Dual File Lists:** The GUI presents two distinct listboxes:

    * **Input Files:** Displays the files selected by the user for processing. 📁

    * **Generated Files:** Shows the output files produced after a successful processing operation. 📊

* **File Information at a Glance:** Both listboxes display not only the file names but also their respective file sizes in kilobytes, providing immediate feedback on file changes (e.g., after compression). 📏

* **Interactive File Access:** Files listed in both the input and generated file sections are clickable. Double-clicking a file will open it using your operating system's default application or launch the file explorer with the file selected. 🖱️📂

* **Integrated Logging:** A dedicated log output area provides real-time feedback on application operations, warnings, and errors. Directory paths mentioned in the logs are clickable, allowing direct navigation to the output folders. 📝🔗

### 2.2. GPX/KML File Processing Capabilities 🗺️

The core strength of the application lies in its ability to handle GPX and KML files with several powerful processing modes:

* **Compression:** Reduce the size of your track files by optimizing the number of track points and cleaning unnecessary metadata. 📉

* **Merging:** Combine multiple GPX/KML files into a single, consolidated GPX file, ideal for creating continuous routes from fragmented data. ➕

* **POI Extraction:** Automatically identify and extract the starting points of tracks and routes from your files, saving them as Waypoints (Points of Interest) in a new GPX file. 📍

## 3. Detailed Features 🔍

### 3.1. File Management 🗃️

* **Adding Input Files:** Use the "Open Files" button or the "File -> Open..." menu option to select one or multiple GPX, KML, or even ZIP archives containing GPX/KML files. The application intelligently extracts and lists valid geographical data files. ➕📂

* **Removing Input Files:**

    * **"Remove Selected" Button:** Select one or more files in the "Input Files" listbox and click this button to remove them from the processing queue. 🗑️

    * **"Clear Input Files" Button:** Remove all files from the "Input Files" list. 🧹

* **Clearing Generated Files:** The "Clear Generated Files" button allows you to empty the output list, useful for managing the display after multiple processing runs. ✨

### 3.2. Processing Logic 🧠

* **Selective Processing:** If you have selected specific files in the "Input Files" list, only those files will be processed when a "Compress," "Merge," or "Extract POIs" operation is initiated. If no files are selected, the application will process all files currently in the input list. ✅

* **Output Directory Management:** Generated files are saved into a new directory, automatically named with a timestamp (e.g., `gpx_processed_YYYY-MM-DD_HHMMSS`), ensuring clean organization of your outputs. This directory path is explicitly logged and made clickable. 📁📅

### 3.3. Data Optimization ⚙️

The underlying processing engine includes sophisticated optimization techniques:

* **Douglas–Peucker Simplification:** Compression and merging simplify each track segment with a configurable tolerance in meters (10 m by default), preserving segment boundaries and endpoints while limiting the geometric deviation. 🤏

* **Metadata Cleaning:** Irrelevant metadata (e.g., time, extensions, comments, descriptions, symbols) is stripped from points, tracks, and routes to further reduce file size and declutter the data. 🧼

* **Elevation Adjustment:**

    * The application attempts to integrate SRTM (Shuttle Radar Topography Mission) elevation data to correct or enhance elevation values in your tracks and waypoints. ⛰️

    * If SRTM data cannot be initialized (e.g., due to network issues or library unavailability), the application gracefully falls back to using the original elevation data present in the GPX/KML files or defaults to zero, ensuring continued functionality. Warnings are logged if SRTM is unavailable. ⚠️

### 3.4. Logging and Configuration 🚦

* **Real-time Logging:** The "Log Output" pane provides detailed information about every operation, helping you monitor progress and troubleshoot issues. 🪵

* **Configurable Log Level:** Adjust the verbosity of the log output (DEBUG, INFO, WARNING, ERROR, CRITICAL) directly from the GUI, allowing you to control the level of detail displayed. 🎚️

* **Settings Dialog:** Access a comprehensive settings dialog from the "Options -> Settings" menu. Here, you can configure various application parameters, including the simplification tolerance, date formats, and other internal settings. Changes made here are saved to `config.yaml` for persistence across sessions. 🔧💾


## 4. Usage ▶️

To run the GUI application, execute the following command in your project's root directory:

### Run with CLI from source

```bash
python -m gpx_kml_converter [OPTIONS] path/to/file.gpx path/to/file.kml
```

### Run with GUI from source

```bash
python -m gpx_kml_converter.gui
```


Once the GUI is launched, you can:

1.  **Open Files:** Click "Open Files" to add GPX/KML files to the input list. ➕📁

2.  **Select Files (Optional):** Click on files in the input list to select them for specific processing. If no files are selected, all loaded input files will be processed. ✅

3.  **Choose a Processing Mode:** Click one of the processing buttons ("Compress," "Merge," "Extract POIs") to start the operation. ▶️

4.  **Monitor Progress:** Observe the log output and the progress bar. ⏳

5.  **View Results:** Check the "Generated Files" list for your processed outputs. Double-click an output file to open it or navigate to its containing directory. 🌟
```