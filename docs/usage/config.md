# Configuration Parameters

These parameters are available to configure the behavior of your application.
The parameters in the cli category can be accessed via the command line interface.

## Category "cli"

| Name              | Type | Description                                       | Default | Choices       |
|-------------------|------|---------------------------------------------------|---------|---------------|
| input             | str  | Path to input (file or folder)                    | ''      | -             |
| output            | str  | Path to output destination                        | ''      | -             |
| min_dist          | int  | Maximum distance between two waypoints            | 20      | -             |
| extract_waypoints | bool | Extract starting points of each track as waypoint | True    | [True, False] |
| elevation         | bool | Include elevation data in waypoints               | True    | [True, False] |

## Category "app"

| Name                   | Type | Description                                 | Default    | Choices                                           |
|------------------------|------|---------------------------------------------|------------|---------------------------------------------------|
| date_format            | str  | Date format to use                          | '%Y-%m-%d' | -                                                 |
| log_level              | str  | Logging level for the application           | 'INFO'     | ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] |
| log_file_max_size      | int  | Maximum log file size in MB before rotation | 10         | -                                                 |
| log_backup_count       | int  | Number of backup log files to keep          | 5          | -                                                 |
| log_format             | str  | Log message format style                    | 'detailed' | ['simple', 'detailed', 'json']                    |
| max_workers            | int  | Maximum number of worker threads            | 4          | -                                                 |
| enable_file_logging    | bool | Enable logging to file                      | True       | [True, False]                                     |
| enable_console_logging | bool | Enable logging to console                   | True       | [True, False]                                     |

## Category "gui"

| Name              | Type | Description                                | Default | Choices                   |
|-------------------|------|--------------------------------------------|---------|---------------------------|
| theme             | str  | GUI theme setting                          | 'light' | ['light', 'dark', 'auto'] |
| window_width      | int  | Default window width                       | 800     | -                         |
| window_height     | int  | Default window height                      | 600     | -                         |
| log_window_height | int  | Height of the log window in pixels         | 200     | -                         |
| auto_scroll_log   | bool | Automatically scroll to newest log entries | True    | [True, False]             |
| max_log_lines     | int  | Maximum number of log lines to keep in GUI | 1000    | -                         |

