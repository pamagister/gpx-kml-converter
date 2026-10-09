# Configuration Parameters

These parameters are available to configure the behavior of your application.
Parameters marked as CLI parameters can also be set via the command line interface.

## Configuration File Reference

The actual configuration is stored in [`config.yaml`](../../config.yaml). You can:

- Edit the configuration file directly using your text editor
- Use the `--config` command-line option to specify a custom config file

## Category "app" {#app}

| Name                   | Type | Description                                 | Default    | Choices                                                                                                                                               |
|------------------------|------|---------------------------------------------|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| date_format            | str  | Date format to use                          | '%Y-%m-%d' | -                                                                                                                                                     |
| log_level              | str  | Logging level for the application           | 'INFO'     | ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']                                                                                                     |
| log_file_max_size      | int  | Maximum log file size in MB before rotation | 2          | -                                                                                                                                                     |
| enable_file_logging    | bool | Enable logging to file                      | True       | [True, False]                                                                                                                                         |
| enable_console_logging | bool | Enable logging to console                   | True       | [True, False]                                                                                                                                         |
| theme                  | str  | GUI theme setting supported by ttkbootstrap | 'darkly'   | ['cosmo', 'flatly', 'litera', 'minty', 'lumen', 'sandstone', 'yeti', 'pulse', 'united', 'darkly', 'superhero', 'solar', 'cyborg', 'vapor', 'simplex'] |

## Category "cli" {#cli}

| Name      | Type  | Description                                                           | Default    | Choices                                          |
|-----------|-------|-----------------------------------------------------------------------|------------|--------------------------------------------------|
| input     | str   | One or more input paths (GPX, KML, ZIP, or directory)                 | ''         | -                                                |
| output    | str   | Output directory override; 'auto' uses mode-specific output locations | 'auto'     | -                                                |
| tolerance | float | Douglas-Peucker simplification tolerance in meters                    | 10.0       | -                                                |
| mode      | str   | Processing operation                                                  | 'compress' | ['compress', 'merge', 'extract-pois', 'add-poi'] |
| recursive | bool  | Search input directories recursively                                  | False      | [True, False]                                    |
| elevation | bool  | Include elevation data in waypoints                                   | True       | [True, False]                                    |

## Category "gui" {#gui}

| Name              | Type | Description                                | Default | Choices                   |
|-------------------|------|--------------------------------------------|---------|---------------------------|
| theme             | str  | GUI theme setting                          | 'light' | ['light', 'dark', 'auto'] |
| window_width      | int  | Default window width                       | 800     | -                         |
| window_height     | int  | Default window height                      | 600     | -                         |
| log_window_height | int  | Height of the log window in pixels         | 200     | -                         |
| auto_scroll_log   | bool | Automatically scroll to newest log entries | True    | [True, False]             |
| max_log_lines     | int  | Maximum number of log lines to keep in GUI | 1000    | -                         |

