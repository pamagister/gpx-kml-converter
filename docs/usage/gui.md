# Graphical user interface (GUI)

The GUI provides a non-destructive workspace for browsing and processing GPX,
KML, and ZIP inputs.

## Workspace and inspection

- Use **Open Files** to add source files. Files appear under **Inputs**; processed
  and edited copies appear under **Generated**.
- Select input file rows to choose a batch. If no input file rows are selected,
  processing uses all loaded inputs. **Select All Inputs** explicitly selects
  every input. Selecting a track, route, or POI changes inspection only.
- Select a file to inspect its track, route, and POI counts and total track
  distance. Select an artifact to inspect its metadata; its containing file is
  shown on the map, and selected tracks also show an elevation profile.
- Double-click a file or artifact to open its source file in the system's
  default application. Double-clicking an unsaved working copy opens its
  unchanged source and records a warning in the log.

## Context menu and removal

Right-click a file or artifact to open its context menu. **Open Containing
Folder** opens the folder containing the physical source. For a file, **Remove
from Workspace** removes the selected file entry from the GUI only; it never
deletes the disk file. Select multiple files to remove them together.

Tracks, routes, and POIs can also be removed. The selection must contain only
one node type; mixed file/artifact or mixed artifact-type selections are
blocked. Selecting a Tracks, Routes, or POIs category removes all items in that
category. Artifact removal creates a new in-memory entry under **Generated**;
the source and its GPX content are not modified. The Delete key performs the
same removal as the context menu.

## Processing

Choose **Process Files**, **Merge Files**, or **Extract POIs from Tracks**.
Generated results remain in the workspace. To process a result in a later
step, select it and choose **Use Selected Results as Inputs**.

By default, **Process Files** writes each result beside its source using
`<source-stem>_processed_<date-time>.gpx`. For files loaded from a ZIP archive,
results go in a sibling directory named after the archive without its
extension; each result uses
`<member-stem>_processed_<date-time>.gpx`. **Merge Files** writes
`gpx_processed_<date-time>.gpx` in the current directory. An explicit output
directory overrides these destinations. Existing output names are overwritten;
duplicate names produced by one batch receive a numeric suffix.

## Main Window Overview

![gui_main.png](../_static/img/gui_main.png)

## Settings Dialog

![gui_settings.png](../_static/img/gui_settings.png)
