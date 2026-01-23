# CAN Data Viewer

A graphical desktop application for visualizing CAN (Controller Area Network) data from BLF (Binary Logging Format) files using DBC (CAN Database) definitions.

![Version](https://img.shields.io/badge/version-1.1.0-blue)
![Python](https://img.shields.io/badge/python-3.7+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

### Core Functionality
- ✅ **BLF File Support**: Read and parse Binary Logging Format files
- ✅ **DBC Database Integration**: Parse DBC files for message and signal definitions
- ✅ **Signal Selection**: Interactive tree view to select messages and signals
- ✅ **Dynamic Multi-Graph Display**: Visualize 1-10 signals simultaneously (configurable)
- ✅ **Time Domain Visualization**: All graphs show signal values over time

### 🆕 Advanced Visualization Features (v1.1.0)
- ✅ **Dynamic Graph Count**: Choose between 1-10 graphs (default: 1)
- ✅ **Dark Mode**: Toggle between light and dark themes for comfortable viewing
- ✅ **Dual Cursor System**: Add up to 2 cursors (green and red) for precise measurements
- ✅ **Cursor Statistics**: Automatic calculation of statistics between cursors:
  - Average, Maximum, Minimum values
  - Standard Deviation
  - Sample count
  - Time range and duration
- ✅ **Synchronized Navigation**: All graphs share synchronized X-axis (time)
- ✅ **Interactive Controls**:
  - Zoom in/out with mouse wheel
  - Pan by right-clicking and dragging
  - Drag cursors to move them
  - Select area to zoom (Y-axis auto-scales)
  - Reset zoom to show all data
- ✅ **Color Coding**: Each graph uses a distinct color for easy identification
- ✅ **Grid and Legends**: Graphs include grid lines and legends with signal names and units

### 🆕 Enhanced Data Management (v1.1.0)
- ✅ **CSV Export**: Export selected signals to CSV format with time column
- ✅ **Partial Data Export**: Export time range between cursors to JSON
- ✅ **Enhanced Workspace**: Save and restore complete work sessions including:
  - File paths (BLF and DBC)
  - Selected signals
  - View range and zoom level
  - Window size and layout
  - Graph count setting
  - Dark mode preference
  - Cursor positions
- ✅ **Graph Export**: Export graphs to PNG, JPEG, and SVG formats
- ✅ **Error Handling**: Robust error handling with user-friendly messages

## Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Steps

1. **Clone the repository**:
```bash
git clone https://github.com/ontoloji/Can_Reader_Vec.git
cd Can_Reader_Vec
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

### Dependencies
The application requires the following Python packages:
- `python-can>=4.2.0` - BLF file reading
- `cantools>=39.4.0` - DBC file parsing
- `matplotlib>=3.7.0` - Plotting support
- `PyQt5>=5.15.9` - GUI framework
- `numpy>=1.24.0` - Numerical operations
- `pyqtgraph>=0.13.0` - High-performance plotting

## Usage

### Starting the Application

Run the main application:
```bash
python main.py
```

### Quick Start Guide

1. **Load Files**:
   - Go to `File → Open BLF File...` and select your BLF file
   - Go to `File → Open DBC File...` and select your DBC file

2. **Configure Display**:
   - In the left panel, adjust "Number of Graphs" spinbox (1-10 graphs)
   - Toggle dark mode via `View → Dark Mode` for comfortable viewing

3. **Select Signals**:
   - In the left panel, expand messages to see available signals
   - Check the boxes next to signals you want to visualize
   - Selected signals will automatically appear in the graphs

4. **Use Cursors for Analysis**:
   - Click `Add Cursor 1 (Green)` in toolbar to add first cursor
   - Click `Add Cursor 2 (Red)` to add second cursor
   - Drag cursors to position them on the graphs
   - View statistics in the "Cursor Statistics" dock (appears when cursors are added)
   - Click `Remove All Cursors` to clear cursors

5. **Navigate Graphs**:
   - **Zoom In**: Scroll up with mouse wheel or drag to select an area
   - **Zoom Out**: Scroll down with mouse wheel
   - **Pan**: Right-click and drag
   - **Reset View**: `View → Reset Zoom` or press `Ctrl+R`

6. **Export Data**:
   - **CSV Export**: `File → Export → Export to CSV...` (exports all signals)
   - **Time Range Export**: `File → Export → Export Time Range...` (requires 2 cursors)
   - **Graph Images**: `File → Export → Export Graphs...`

7. **Save/Load Workspace**:
   - `File → Save Workspace...` - Save current session (includes cursors, theme, graph count)
   - `File → Load Workspace...` - Restore a previous session

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+B` | Open BLF File |
| `Ctrl+D` | Open DBC File |
| `Ctrl+S` | Save Workspace |
| `Ctrl+L` | Load Workspace |
| `Ctrl+E` | Export Graphs |
| `Ctrl+Shift+C` | Export to CSV |
| `Ctrl+R` | Reset Zoom |
| `Ctrl+F` | Fit to Data |
| `Ctrl+Q` | Exit Application |
| `F1` | User Guide |

## Project Structure

```
can_viewer_app/
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .gitignore                  # Git ignore rules
│
├── gui/                        # GUI components
│   ├── __init__.py
│   ├── main_window.py          # Main application window with menus/toolbar
│   ├── signal_selector.py      # Signal selection tree widget + graph count
│   ├── graph_panel.py          # Dynamic graph display panel (1-10 graphs)
│   ├── dialogs.py              # About and user guide dialogs
│   ├── theme_manager.py        # 🆕 Dark/light theme management
│   ├── cursor_manager.py       # 🆕 Dual cursor system
│   └── statistics_widget.py    # 🆕 Cursor statistics display
│
├── data/                       # Data processing
│   ├── __init__.py
│   ├── blf_reader.py           # BLF file reader
│   ├── dbc_parser.py           # DBC file parser
│   └── signal_processor.py     # Signal decoding and processing
│
├── utils/                      # Utility modules
│   ├── __init__.py
│   ├── config.py               # Application configuration
│   ├── workspace.py            # Enhanced workspace save/load
│   ├── export.py               # Graph export functionality
│   ├── csv_exporter.py         # 🆕 CSV data export
│   └── partial_exporter.py     # 🆕 JSON time range export
│
└── resources/                  # Application resources
    └── icons/                  # Icon files (optional)
```

## Technical Details

### Architecture

The application follows a modular architecture:

1. **Data Layer** (`data/`):
   - `BLFReader`: Handles BLF file reading using python-can
   - `DBCParser`: Parses DBC files using cantools
   - `SignalProcessor`: Decodes signals and prepares data for visualization

2. **GUI Layer** (`gui/`):
   - `MainWindow`: Main application window with menus, toolbar, and layout
   - `SignalSelector`: Tree widget for message/signal selection + graph count control
   - `GraphPanel`: Container for 1-10 dynamically created PyQtGraph plots
   - `CursorManager`: Manages synchronized cursors across all graphs
   - `StatisticsWidget`: Displays statistics between cursor positions
   - `ThemeManager`: Handles dark/light theme switching
   - `Dialogs`: About and user guide dialogs

3. **Utilities** (`utils/`):
   - `Workspace`: JSON-based workspace save/load (enhanced with new settings)
   - `CSVExporter`: Export signal data to CSV format
   - `PartialDataExporter`: Export time range data to JSON
   - `GraphExporter`: Export graphs to various image formats
   - `config`: Application-wide constants and settings

### Data Flow

1. User loads BLF and DBC files
2. Application extracts message IDs from BLF
3. DBC definitions are matched with BLF message IDs
4. Available messages/signals are displayed in tree view
5. User selects signals (up to 5)
6. SignalProcessor decodes selected signals
7. Graphs display time-series data with synchronized navigation

### Performance Optimizations

- **Lazy Loading**: Large BLF files are processed on-demand
- **PyQtGraph**: High-performance plotting library for smooth interaction
- **Caching**: Decoded signals are cached to avoid reprocessing
- **NumPy Arrays**: Efficient numerical data handling

## Troubleshooting

### Common Issues

**Problem**: "Failed to load BLF file"
- **Solution**: Ensure the file is a valid BLF (Binary Logging Format) file
- Check file permissions

**Problem**: "Failed to load DBC file"
- **Solution**: Verify the DBC file syntax is correct
- Ensure the file is a valid CAN database file

**Problem**: "No signals available"
- **Solution**: Check that the BLF file contains messages that match the DBC definitions
- Verify message IDs match between BLF and DBC

**Problem**: "Cannot add more graphs"
- **Solution**: Maximum 10 graphs can be displayed
- Use the "Number of Graphs" spinbox to adjust the count

**Problem**: "Cursor already exists"
- **Solution**: Remove existing cursors before adding new ones
- Use "Remove All Cursors" button in toolbar

**Problem**: "Cannot export time range"
- **Solution**: Add 2 cursors to define the time range before exporting
- Ensure signals are selected

### Error Messages

The application provides user-friendly error messages for common issues:
- File loading failures
- Invalid file formats
- DBC-BLF message ID mismatches
- Maximum signal selection exceeded

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is licensed under the MIT License.

## Acknowledgments

- **python-can**: For BLF file support
- **cantools**: For DBC parsing capabilities
- **PyQt5**: For the GUI framework
- **pyqtgraph**: For high-performance plotting

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the User Guide (`Help → User Guide` in the application)

## Version History

### v1.1.0 (Advanced Graphics Features)
- 🆕 Dynamic graph count control (1-10 graphs, configurable)
- 🆕 Dark mode theme with persistent preference
- 🆕 Dual cursor system (green and red cursors)
- 🆕 Cursor statistics widget with real-time calculations
- 🆕 CSV export functionality
- 🆕 Partial data export (JSON format for time ranges)
- 🆕 Enhanced workspace save/load (includes theme, cursors, graph count)
- ✨ Improved graph panel with dynamic recreation
- ✨ Y-axis auto-scaling on zoom
- ✨ Synchronized cursor movement across all graphs

### v1.0.0 (Initial Release)
- BLF and DBC file support
- Up to 5 simultaneous signal displays
- Synchronized zoom and pan
- Workspace save/load
- Graph export (PNG, JPEG, SVG)
- User guide and documentation
