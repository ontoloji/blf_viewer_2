"""
Main Window Module
Main application window for the CAN Data Viewer.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QAction, QFileDialog, QMessageBox, QDockWidget, QApplication
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QKeySequence
import os

from gui.signal_selector import SignalSelector
from gui.graph_panel import GraphPanel
from gui.dialogs import AboutDialog, UserGuideDialog
from gui.raw_data_viewer import RawDataViewerDialog
from gui.cursor_manager import CursorManager
from gui.statistics_widget import StatisticsWidget
from gui.theme_manager import ThemeManager
from data.blf_reader import BLFReader
from data.dbc_parser import DBCParser
from data.signal_processor import SignalProcessor
from utils.workspace import Workspace
from utils.export import GraphExporter
from utils.csv_exporter import CSVExporter
from utils.partial_exporter import PartialDataExporter


class MainWindow(QMainWindow):
    """Main application window for CAN Data Viewer."""
    
    def __init__(self):
        super().__init__()
        
        # Data objects
        self.blf_reader = BLFReader()
        self.dbc_parser = DBCParser()
        self.signal_processor = None
        
        # File paths
        self.blf_path = None
        self.dbc_path = None
        
        # Last used directories
        self.last_blf_dir = None
        self.last_dbc_dir = None
        
        # Settings
        self.settings = QSettings('CAN Tools', 'CAN Data Viewer')
        
        # GUI components
        self.signal_selector = None
        self.graph_panel = None
        self.cursor_manager = None
        self.statistics_widget = None
        self.statistics_dock = None
        self.overlay_mode_enabled = False
        
        # Initialize UI
        self.init_ui()
        
        # Load settings
        self.load_settings()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("CAN Data Viewer")
        self.resize(1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create splitter for left panel (signal selector) and right panel (graphs)
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Signal Selector
        self.signal_selector = SignalSelector(max_signals=5)
        self.signal_selector.selection_changed.connect(self.on_signal_selection_changed)
        self.signal_selector.graph_count_changed.connect(self.on_graph_count_changed)
        self.signal_selector.overlay_mode_changed.connect(self.on_overlay_mode_changed)
        splitter.addWidget(self.signal_selector)
        
        # Right panel: Graph Panel
        self.graph_panel = GraphPanel(max_graphs=10)
        splitter.addWidget(self.graph_panel)
        
        # Set splitter proportions (25% left, 75% right)
        splitter.setSizes([300, 900])
        
        main_layout.addWidget(splitter)
        
        # Create cursor manager
        self.cursor_manager = CursorManager(self.graph_panel.plot_widgets)
        self.cursor_manager.cursor_moved.connect(self.on_cursor_moved)
        
        # Create statistics dock widget (hidden by default)
        self.statistics_dock = QDockWidget("Cursor Statistics", self)
        self.statistics_widget = StatisticsWidget()
        self.statistics_dock.setWidget(self.statistics_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.statistics_dock)
        self.statistics_dock.setVisible(False)
        
        # Create menus and toolbar
        self.create_menus()
        self.create_toolbar()
        
        # Create status bar
        self.statusBar().showMessage("Ready")
    
    def create_menus(self):
        """Create application menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # Open BLF file
        open_blf_action = QAction('Open &BLF File...', self)
        open_blf_action.setShortcut(QKeySequence('Ctrl+B'))
        open_blf_action.triggered.connect(self.open_blf_file)
        file_menu.addAction(open_blf_action)
        
        # Open DBC file
        open_dbc_action = QAction('Open &DBC File...', self)
        open_dbc_action.setShortcut(QKeySequence('Ctrl+D'))
        open_dbc_action.triggered.connect(self.open_dbc_file)
        file_menu.addAction(open_dbc_action)
        
        file_menu.addSeparator()
        
        # Save workspace
        save_workspace_action = QAction('&Save Workspace...', self)
        save_workspace_action.setShortcut(QKeySequence('Ctrl+S'))
        save_workspace_action.triggered.connect(self.save_workspace)
        file_menu.addAction(save_workspace_action)
        
        # Load workspace
        load_workspace_action = QAction('&Load Workspace...', self)
        load_workspace_action.setShortcut(QKeySequence('Ctrl+L'))
        load_workspace_action.triggered.connect(self.load_workspace)
        file_menu.addAction(load_workspace_action)
        
        file_menu.addSeparator()
        
        # Export submenu
        export_menu = file_menu.addMenu('&Export')
        
        export_graphs_action = QAction('Export &Graphs...', self)
        export_graphs_action.setShortcut(QKeySequence('Ctrl+E'))
        export_graphs_action.triggered.connect(self.export_graphs)
        export_menu.addAction(export_graphs_action)
        
        export_csv_action = QAction('Export to &CSV...', self)
        export_csv_action.setShortcut(QKeySequence('Ctrl+Shift+C'))
        export_csv_action.triggered.connect(self.export_to_csv)
        export_menu.addAction(export_csv_action)
        
        export_time_range_action = QAction('Export &Time Range...', self)
        export_time_range_action.triggered.connect(self.export_time_range)
        export_menu.addAction(export_time_range_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut(QKeySequence('Ctrl+Q'))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('&View')
        
        # Raw data viewer
        view_raw_action = QAction('View &Raw BLF Data...', self)
        view_raw_action.setShortcut('Ctrl+Shift+R')
        view_raw_action.triggered.connect(self.view_raw_data)
        view_menu.addAction(view_raw_action)
        
        view_menu.addSeparator()
        
        # Dark mode toggle
        self.dark_mode_action = QAction('&Dark Mode', self)
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.toggled.connect(self.toggle_dark_mode)
        view_menu.addAction(self.dark_mode_action)
        
        view_menu.addSeparator()
        
        # Reset zoom
        reset_zoom_action = QAction('&Reset Zoom', self)
        reset_zoom_action.setShortcut(QKeySequence('Ctrl+R'))
        reset_zoom_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(reset_zoom_action)
        
        # Fit to data
        fit_data_action = QAction('&Fit to Data', self)
        fit_data_action.setShortcut(QKeySequence('Ctrl+F'))
        fit_data_action.triggered.connect(self.fit_to_data)
        view_menu.addAction(fit_data_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        # User guide
        user_guide_action = QAction('&User Guide', self)
        user_guide_action.setShortcut(QKeySequence('F1'))
        user_guide_action.triggered.connect(self.show_user_guide)
        help_menu.addAction(user_guide_action)
        
        help_menu.addSeparator()
        
        # About
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Create application toolbar."""
        toolbar = self.addToolBar('Main Toolbar')
        toolbar.setMovable(False)
        
        # Add Cursor 1 (Green)
        add_cursor1_action = QAction('Add Cursor 1 (Green)', self)
        add_cursor1_action.triggered.connect(self.add_cursor_1)
        toolbar.addAction(add_cursor1_action)
        
        # Add Cursor 2 (Red)
        add_cursor2_action = QAction('Add Cursor 2 (Red)', self)
        add_cursor2_action.triggered.connect(self.add_cursor_2)
        toolbar.addAction(add_cursor2_action)
        
        # Remove all cursors
        remove_cursors_action = QAction('Remove All Cursors', self)
        remove_cursors_action.triggered.connect(self.remove_all_cursors)
        toolbar.addAction(remove_cursors_action)
    
    def open_blf_file(self):
        """Open BLF file dialog and load the file."""
        start_dir = self.last_blf_dir or os.path.expanduser('~')
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open BLF File",
            start_dir,
            "BLF Files (*.blf);;All Files (*)"
        )
        
        if filepath:
            self.last_blf_dir = os.path.dirname(filepath)
            if self.blf_reader.load_file(filepath):
                self.blf_path = filepath
                self.statusBar().showMessage(f"Loaded BLF: {os.path.basename(filepath)}")
                self.update_signal_list()
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to load BLF file:\n{filepath}"
                )
    
    def open_dbc_file(self):
        """Open DBC file dialog and load the file."""
        start_dir = self.last_dbc_dir or os.path.expanduser('~')
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open DBC File",
            start_dir,
            "DBC Files (*.dbc);;All Files (*)"
        )
        
        if filepath:
            self.last_dbc_dir = os.path.dirname(filepath)
            if self.dbc_parser.load_file(filepath):
                self.dbc_path = filepath
                self.statusBar().showMessage(f"Loaded DBC: {os.path.basename(filepath)}")
                self.update_signal_list()
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to load DBC file:\n{filepath}"
                )
    
    def update_signal_list(self):
        """Update the signal list when BLF or DBC changes."""
        if self.blf_path and self.dbc_path:
            # Create signal processor
            self.signal_processor = SignalProcessor(self.blf_reader, self.dbc_parser)
            
            # Get messages and available IDs
            messages = self.dbc_parser.get_messages()
            available_ids = self.blf_reader.get_unique_message_ids()
            
            # Load into signal selector
            self.signal_selector.load_messages(messages, available_ids)
    
    def on_signal_selection_changed(self, selected_signals):
        """Handle signal selection changes."""
        if not self.signal_processor:
            return
        
        # Clear all graphs first
        self.graph_panel.clear_all()
        
        if self.overlay_mode_enabled:
            for idx, signal_info in enumerate(selected_signals):
                try:
                    time_data, value_data = self.signal_processor.process_signal(
                        signal_info['message'],
                        signal_info['signal']
                    )

                    self.graph_panel.plot_signal(
                        0,
                        time_data,
                        value_data,
                        signal_info,
                        append=idx > 0
                    )

                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Signal Processing Error",
                        f"Failed to process signal {signal_info['signal']}:\n{str(e)}"
                    )
        else:
            # Plot each selected signal
            for idx, signal_info in enumerate(selected_signals):
                if idx >= self.graph_panel.current_graph_count:
                    break
                
                try:
                    # Process signal
                    time_data, value_data = self.signal_processor.process_signal(
                        signal_info['message'],
                        signal_info['signal']
                    )
                    
                    # Plot signal
                    self.graph_panel.plot_signal(idx, time_data, value_data, signal_info)
                    
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Signal Processing Error",
                        f"Failed to process signal {signal_info['signal']}:\n{str(e)}"
                    )
        
        # Update status
        if self.overlay_mode_enabled:
            self.statusBar().showMessage(
                f"Plotting {len(selected_signals)} signal(s) on one combined graph"
            )
        else:
            self.statusBar().showMessage(
                f"Plotting {len(selected_signals)} signal(s)"
            )

        # Keep cursor statistics in sync with newly plotted signals
        self.update_statistics()
    
    def on_graph_count_changed(self, count):
        """Handle graph count changes."""
        self.graph_panel.set_graph_count(count)
        
        # Update cursor manager with new plot widgets
        self.cursor_manager.update_plot_widgets(self.graph_panel.plot_widgets)
        
        # Re-plot selected signals
        selected_signals = self.signal_selector.get_selected_signals()
        self.on_signal_selection_changed(selected_signals)

    def on_overlay_mode_changed(self, enabled):
        """Handle overlay mode toggle."""
        self.overlay_mode_enabled = enabled
        self.on_signal_selection_changed(self.signal_selector.get_selected_signals())
    
    def add_cursor_1(self):
        """Add cursor 1 (green)."""
        if self.cursor_manager.has_cursor(1):
            QMessageBox.information(
                self,
                "Cursor Exists",
                "Cursor 1 is already added."
            )
            return
        
        # Add cursor at middle of view range
        view_range = self.graph_panel.get_view_range()
        if view_range:
            x_min = view_range['x_min']
            x_max = view_range['x_max']
            position = (x_min + x_max) / 4
        else:
            position = 0
        
        self.cursor_manager.add_cursor(1, 'green', position)
        self.check_statistics_visibility()
    
    def add_cursor_2(self):
        """Add cursor 2 (red)."""
        if self.cursor_manager.has_cursor(2):
            QMessageBox.information(
                self,
                "Cursor Exists",
                "Cursor 2 is already added."
            )
            return
        
        # Add cursor at middle of view range
        view_range = self.graph_panel.get_view_range()
        if view_range:
            x_min = view_range['x_min']
            x_max = view_range['x_max']
            position = (x_min + x_max) * 3 / 4
        else:
            position = 0
        
        self.cursor_manager.add_cursor(2, 'red', position)
        self.check_statistics_visibility()
    
    def remove_all_cursors(self):
        """Remove all cursors."""
        self.cursor_manager.remove_all_cursors()
        self.statistics_widget.clear_statistics()
        self.statistics_dock.setVisible(False)
    
    def on_cursor_moved(self, cursor_id, position):
        """Handle cursor movement."""
        self.update_statistics()
    
    def update_statistics(self):
        """Update statistics display."""
        cursor_positions = self.cursor_manager.get_cursor_positions()
        
        if len(cursor_positions) >= 1:
            signal_data = self.graph_panel.get_signal_data()
            self.statistics_widget.update_statistics(cursor_positions, signal_data)
    
    def check_statistics_visibility(self):
        """Show/hide statistics dock based on cursor count."""
        cursor_positions = self.cursor_manager.get_cursor_positions()
        
        if len(cursor_positions) >= 1:
            self.statistics_dock.setVisible(True)
            self.update_statistics()
        else:
            self.statistics_dock.setVisible(False)
    
    def view_raw_data(self):
        """Open raw BLF data viewer dialog."""
        if not self.blf_path:
            QMessageBox.warning(
                self,
                "No BLF File",
                "Please load a BLF file first."
            )
            return
        
        dialog = RawDataViewerDialog(self.blf_reader, self)
        dialog.exec_()
    
    def toggle_dark_mode(self, enabled):
        """Toggle dark mode."""
        app = QApplication.instance()
        
        if enabled:
            ThemeManager.apply_dark_theme(app)
        else:
            ThemeManager.apply_light_theme(app)
        
        # Update graph panel theme
        self.graph_panel.set_theme(enabled)
    
    def reset_zoom(self):
        """Reset zoom on all graphs."""
        self.graph_panel.reset_zoom()
    
    def fit_to_data(self):
        """Fit all graphs to data."""
        self.graph_panel.fit_to_data()
    
    def save_workspace(self):
        """Save current workspace to file."""
        if not self.blf_path or not self.dbc_path:
            QMessageBox.warning(
                self,
                "No Files Loaded",
                "Please load BLF and DBC files first."
            )
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Workspace",
            "workspace.workspace",
            "Workspace Files (*.workspace);;All Files (*)"
        )
        
        if filepath:
            try:
                # Get view range
                view_range = self.graph_panel.get_view_range()
                x_min = view_range.get('x_min', 0)
                x_max = view_range.get('x_max', 0)
                
                # Get cursor positions
                cursor_positions = self.cursor_manager.get_cursor_positions()
                
                # Create workspace data
                workspace_data = Workspace.create_workspace_data(
                    blf_path=self.blf_path,
                    dbc_path=self.dbc_path,
                    selected_signals=self.signal_selector.get_selected_signals(),
                    x_min=x_min,
                    x_max=x_max,
                    window_width=self.width(),
                    window_height=self.height(),
                    graph_count=self.signal_selector.get_graph_count(),
                    dark_mode=self.dark_mode_action.isChecked(),
                    cursor_positions=cursor_positions,
                    overlay_mode=self.signal_selector.is_overlay_mode_enabled()
                )
                
                # Save workspace
                Workspace.save(filepath, workspace_data)
                
                QMessageBox.information(
                    self,
                    "Success",
                    "Workspace saved successfully!"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to save workspace:\n{str(e)}"
                )
    
    def load_workspace(self):
        """Load workspace from file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Load Workspace",
            "",
            "Workspace Files (*.workspace);;All Files (*)"
        )
        
        if filepath:
            try:
                # Load workspace data
                workspace_data = Workspace.load(filepath)
                
                # Load BLF file
                if workspace_data.get('blf_path'):
                    if self.blf_reader.load_file(workspace_data['blf_path']):
                        self.blf_path = workspace_data['blf_path']
                
                # Load DBC file
                if workspace_data.get('dbc_path'):
                    if self.dbc_parser.load_file(workspace_data['dbc_path']):
                        self.dbc_path = workspace_data['dbc_path']
                
                # Update signal list
                self.update_signal_list()
                
                # Restore graph count
                if 'graph_count' in workspace_data:
                    self.signal_selector.set_graph_count(workspace_data['graph_count'])

                # Restore overlay mode
                if 'overlay_mode' in workspace_data:
                    self.signal_selector.set_overlay_mode(workspace_data['overlay_mode'])
                
                # Restore dark mode
                if 'dark_mode' in workspace_data:
                    self.dark_mode_action.setChecked(workspace_data['dark_mode'])
                
                # Restore selected signals
                if workspace_data.get('selected_signals'):
                    self.signal_selector.set_selected_signals(workspace_data['selected_signals'])
                
                # Restore view range
                if 'view_range' in workspace_data:
                    view_range = workspace_data['view_range']
                    self.graph_panel.set_view_range(view_range['x_min'], view_range['x_max'])
                
                # Restore window geometry
                if 'window_geometry' in workspace_data:
                    geom = workspace_data['window_geometry']
                    self.resize(geom['width'], geom['height'])
                
                # Restore cursors
                if 'cursor_positions' in workspace_data:
                    cursor_positions = workspace_data['cursor_positions']
                    for cursor_id, position in cursor_positions.items():
                        cursor_id = int(cursor_id)
                        color = 'green' if cursor_id == 1 else 'red'
                        self.cursor_manager.add_cursor(cursor_id, color, position)
                    self.check_statistics_visibility()
                
                QMessageBox.information(
                    self,
                    "Success",
                    "Workspace loaded successfully!"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to load workspace:\n{str(e)}"
                )
    
    def export_graphs(self):
        """Export graphs to image files."""
        if not self.graph_panel.plot_widgets:
            QMessageBox.warning(
                self,
                "No Graphs",
                "No graphs to export."
            )
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Graphs",
            "graph.png",
            "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;SVG Files (*.svg);;All Files (*)"
        )
        
        if filepath:
            try:
                self.graph_panel.export_all(filepath)
                QMessageBox.information(
                    self,
                    "Success",
                    f"Graphs exported successfully!"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to export graphs:\n{str(e)}"
                )
    
    def export_to_csv(self):
        """Export signal data to CSV."""
        selected_signals = self.signal_selector.get_selected_signals()
        
        if not selected_signals:
            QMessageBox.warning(
                self,
                "No Signals",
                "Please select signals to export."
            )
            return
        
        # Check if we should export time range
        cursor_positions = self.cursor_manager.get_cursor_positions()
        time_range = None
        
        if len(cursor_positions) == 2:
            reply = QMessageBox.question(
                self,
                "Export Time Range",
                "Export only data between cursors?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                positions = sorted(cursor_positions.values())
                time_range = (positions[0], positions[1])
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export to CSV",
            "signals.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if filepath:
            try:
                CSVExporter.export(
                    filepath,
                    self.signal_processor,
                    selected_signals,
                    time_range
                )
                
                QMessageBox.information(
                    self,
                    "Success",
                    "Data exported to CSV successfully!"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to export to CSV:\n{str(e)}"
                )
    
    def export_time_range(self):
        """Export time range data to JSON."""
        cursor_positions = self.cursor_manager.get_cursor_positions()
        
        if len(cursor_positions) != 2:
            QMessageBox.warning(
                self,
                "Cursors Required",
                "Please add 2 cursors to define the time range."
            )
            return
        
        selected_signals = self.signal_selector.get_selected_signals()
        
        if not selected_signals:
            QMessageBox.warning(
                self,
                "No Signals",
                "Please select signals to export."
            )
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Time Range",
            "time_range.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if filepath:
            try:
                positions = sorted(cursor_positions.values())
                time_range = (positions[0], positions[1])
                
                PartialDataExporter.export(
                    filepath,
                    self.signal_processor,
                    selected_signals,
                    time_range,
                    self.blf_path,
                    self.dbc_path
                )
                
                QMessageBox.information(
                    self,
                    "Success",
                    "Time range data exported successfully!"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to export time range:\n{str(e)}"
                )
    
    def show_user_guide(self):
        """Show user guide dialog."""
        dialog = UserGuideDialog(self)
        dialog.exec_()
    
    def show_about(self):
        """Show about dialog."""
        dialog = AboutDialog(self)
        dialog.exec_()
    
    def load_settings(self):
        """Load application settings."""
        # Load window geometry
        if self.settings.contains('geometry'):
            self.restoreGeometry(self.settings.value('geometry'))
        
        # Load last directories
        self.last_blf_dir = self.settings.value('last_blf_dir', None)
        self.last_dbc_dir = self.settings.value('last_dbc_dir', None)
        
        # Load dark mode preference
        dark_mode = self.settings.value('dark_mode', False, type=bool)
        self.dark_mode_action.setChecked(dark_mode)
    
    def save_settings(self):
        """Save application settings."""
        # Save window geometry
        self.settings.setValue('geometry', self.saveGeometry())
        
        # Save last directories
        if self.last_blf_dir:
            self.settings.setValue('last_blf_dir', self.last_blf_dir)
        if self.last_dbc_dir:
            self.settings.setValue('last_dbc_dir', self.last_dbc_dir)
        
        # Save dark mode preference
        self.settings.setValue('dark_mode', self.dark_mode_action.isChecked())
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Save settings
        self.save_settings()
        
        # Accept the event
        event.accept()
