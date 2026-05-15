"""
Signal Selector Widget
Left panel for selecting CAN messages and signals.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QMessageBox, QSpinBox, QHBoxLayout, QCheckBox, QComboBox
)
from PyQt5.QtCore import pyqtSignal, Qt
from typing import List, Dict, Any, Optional


class SignalSelector(QWidget):
    """Widget for selecting CAN signals from a tree view."""
    
    # Signal emitted when selection changes
    selection_changed = pyqtSignal(list)
    # Signal emitted when graph count changes
    graph_count_changed = pyqtSignal(int)
    # Signal emitted when overlay mode changes
    overlay_mode_changed = pyqtSignal(bool)
    # Signal emitted when XY mode changes
    xy_mode_changed = pyqtSignal(bool)
    # Signal emitted when XY axis mapping changes
    xy_axes_changed = pyqtSignal(dict)
    
    def __init__(self, max_signals: int = 5):
        super().__init__()
        self.max_signals = max_signals
        self.selected_signals: List[Dict[str, str]] = []
        self.xy_mode_enabled = False
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Title label
        title_label = QLabel("Signal Selection")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # Graph count selection
        graph_count_layout = QHBoxLayout()
        graph_count_label = QLabel("Number of Graphs:")
        graph_count_layout.addWidget(graph_count_label)
        
        self.graph_count_spinbox = QSpinBox()
        self.graph_count_spinbox.setMinimum(1)
        self.graph_count_spinbox.setMaximum(10)
        self.graph_count_spinbox.setValue(1)  # Default 1 graph
        self.graph_count_spinbox.setToolTip("Select number of graphs to display (1-10)")
        self.graph_count_spinbox.valueChanged.connect(self.on_graph_count_changed)
        graph_count_layout.addWidget(self.graph_count_spinbox)
        graph_count_layout.addStretch()
        
        layout.addLayout(graph_count_layout)

        self.overlay_checkbox = QCheckBox("Overlay selected signals on one graph")
        self.overlay_checkbox.setToolTip(
            "Useful for comparing signals such as SOC and current on the same graph."
        )
        self.overlay_checkbox.toggled.connect(self.on_overlay_mode_changed)
        layout.addWidget(self.overlay_checkbox)

        self.xy_mode_checkbox = QCheckBox("Enable X-Y Relation Plot")
        self.xy_mode_checkbox.setToolTip(
            "Plot one signal against another by aligning them on time."
        )
        self.xy_mode_checkbox.toggled.connect(self.on_xy_mode_changed)
        layout.addWidget(self.xy_mode_checkbox)

        xy_axes_layout = QHBoxLayout()
        self.x_axis_combo = QComboBox()
        self.y_axis_combo = QComboBox()
        self.x_axis_combo.setToolTip("Select signal for X axis")
        self.y_axis_combo.setToolTip("Select signal for Y axis")
        self.x_axis_combo.currentIndexChanged.connect(self.emit_xy_axes_changed)
        self.y_axis_combo.currentIndexChanged.connect(self.emit_xy_axes_changed)
        xy_axes_layout.addWidget(QLabel("X:"))
        xy_axes_layout.addWidget(self.x_axis_combo)
        xy_axes_layout.addWidget(QLabel("Y:"))
        xy_axes_layout.addWidget(self.y_axis_combo)
        layout.addLayout(xy_axes_layout)
        
        # Tree widget for messages and signals
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Message / Signal", "ID / Unit"])
        self.tree.itemChanged.connect(self.on_item_changed)
        layout.addWidget(self.tree)
        
        # Selected signals label
        self.selected_label = QLabel(f"Selected: 0/{self.max_signals}")
        layout.addWidget(self.selected_label)
        
        # Clear selection button
        clear_btn = QPushButton("Clear Selection")
        clear_btn.clicked.connect(self.clear_selection)
        layout.addWidget(clear_btn)
        
        self.setLayout(layout)
        self._refresh_xy_axis_choices()
        self.x_axis_combo.setEnabled(False)
        self.y_axis_combo.setEnabled(False)
    
    def load_messages(self, messages: List[Dict[str, Any]], available_ids: List[int]):
        """
        Load messages from DBC and highlight those available in BLF.
        
        Args:
            messages: List of message dictionaries from DBC parser
            available_ids: List of message IDs available in BLF file
        """
        self.tree.clear()
        self.tree.setColumnWidth(0, 200)
        
        available_id_set = set(available_ids)
        
        for msg in messages:
            msg_id = msg['id']
            is_available = msg_id in available_id_set
            
            # Create message item
            msg_item = QTreeWidgetItem(self.tree)
            msg_item.setText(0, msg['name'])
            msg_item.setText(1, f"0x{msg_id:X}")
            msg_item.setData(0, Qt.UserRole, {'type': 'message', 'name': msg['name'], 'id': msg_id})
            
            # Gray out unavailable messages
            if not is_available:
                for col in range(2):
                    msg_item.setForeground(col, Qt.gray)
                msg_item.setToolTip(0, "Not available in BLF file")
            
            # Add signal items
            for sig in msg['signals']:
                sig_item = QTreeWidgetItem(msg_item)
                sig_item.setText(0, sig['name'])
                sig_item.setText(1, sig['unit'])
                sig_item.setData(0, Qt.UserRole, {
                    'type': 'signal',
                    'message': msg['name'],
                    'name': sig['name'],
                    'unit': sig['unit']
                })
                
                # Only allow selection if message is available
                if is_available:
                    sig_item.setFlags(sig_item.flags() | Qt.ItemIsUserCheckable)
                    sig_item.setCheckState(0, Qt.Unchecked)
                else:
                    for col in range(2):
                        sig_item.setForeground(col, Qt.gray)
    
    def on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle item check state changes."""
        data = item.data(0, Qt.UserRole)
        
        if data and data['type'] == 'signal':
            if item.checkState(0) == Qt.Checked:
                # Check if we can add more signals
                if len(self.selected_signals) >= self.max_signals:
                    item.setCheckState(0, Qt.Unchecked)
                    QMessageBox.warning(
                        self,
                        "Maximum Signals",
                        f"Maximum {self.max_signals} signals can be selected."
                    )
                    return
                
                # Add to selected signals
                signal_info = {
                    'message': data['message'],
                    'signal': data['name'],
                    'unit': data['unit']
                }
                self.selected_signals.append(signal_info)
            else:
                # Remove from selected signals
                signal_info = {
                    'message': data['message'],
                    'signal': data['name'],
                    'unit': data['unit']
                }
                if signal_info in self.selected_signals:
                    self.selected_signals.remove(signal_info)
            
            # Update label and emit signal
            self.update_selection_label()
            self._refresh_xy_axis_choices()
            self.selection_changed.emit(self.selected_signals)
    
    def clear_selection(self):
        """Clear all selected signals."""
        # Uncheck all items
        for i in range(self.tree.topLevelItemCount()):
            msg_item = self.tree.topLevelItem(i)
            for j in range(msg_item.childCount()):
                sig_item = msg_item.child(j)
                sig_item.setCheckState(0, Qt.Unchecked)
        
        self.selected_signals.clear()
        self.update_selection_label()
        self._refresh_xy_axis_choices()
        self.selection_changed.emit(self.selected_signals)
    
    def update_selection_label(self):
        """Update the selected signals count label."""
        self.selected_label.setText(
            f"Selected: {len(self.selected_signals)}/{self.max_signals}"
        )
    
    def get_selected_signals(self) -> List[Dict[str, str]]:
        """Get the list of selected signals."""
        return self.selected_signals
    
    def set_selected_signals(self, signals: List[Dict[str, str]]):
        """
        Set selected signals (used when loading workspace).
        
        Args:
            signals: List of signal dictionaries
        """
        self.clear_selection()
        
        # Find and check the items
        for sig_info in signals:
            if len(self.selected_signals) >= self.max_signals:
                break
            
            for i in range(self.tree.topLevelItemCount()):
                msg_item = self.tree.topLevelItem(i)
                msg_data = msg_item.data(0, Qt.UserRole)
                
                if msg_data and msg_data['name'] == sig_info['message']:
                    for j in range(msg_item.childCount()):
                        sig_item = msg_item.child(j)
                        sig_data = sig_item.data(0, Qt.UserRole)
                        
                        if sig_data and sig_data['name'] == sig_info['signal']:
                            sig_item.setCheckState(0, Qt.Checked)
                            break
                    break
    
    def on_graph_count_changed(self, value: int):
        """
        Handle graph count change.
        
        Args:
            value: New graph count value
        """
        self.graph_count_changed.emit(value)

    def on_overlay_mode_changed(self, enabled: bool):
        """Handle overlay mode change."""
        self.overlay_mode_changed.emit(enabled)

    def on_xy_mode_changed(self, enabled: bool):
        """Handle XY mode toggle."""
        self.xy_mode_enabled = enabled
        self.overlay_checkbox.setEnabled(not enabled)
        self.graph_count_spinbox.setEnabled(not enabled)
        self.x_axis_combo.setEnabled(enabled)
        self.y_axis_combo.setEnabled(enabled)
        self.xy_mode_changed.emit(enabled)
        self.emit_xy_axes_changed()

    def _refresh_xy_axis_choices(self):
        """Refresh available X/Y axis signal choices from selected signals."""
        previous_x = self.x_axis_combo.currentText()
        previous_y = self.y_axis_combo.currentText()

        self.x_axis_combo.blockSignals(True)
        self.y_axis_combo.blockSignals(True)

        self.x_axis_combo.clear()
        self.y_axis_combo.clear()

        for signal in self.selected_signals:
            key = f"{signal['message']}.{signal['signal']}"
            self.x_axis_combo.addItem(key, signal)
            self.y_axis_combo.addItem(key, signal)

        if self.x_axis_combo.count() > 0:
            x_index = self.x_axis_combo.findText(previous_x)
            self.x_axis_combo.setCurrentIndex(x_index if x_index >= 0 else 0)

        if self.y_axis_combo.count() > 0:
            y_index = self.y_axis_combo.findText(previous_y)
            default_y = 1 if self.y_axis_combo.count() > 1 else 0
            self.y_axis_combo.setCurrentIndex(y_index if y_index >= 0 else default_y)

        self.x_axis_combo.blockSignals(False)
        self.y_axis_combo.blockSignals(False)

        self.emit_xy_axes_changed()

    def emit_xy_axes_changed(self):
        """Emit selected axis mapping for XY mode consumers."""
        x_signal = self.x_axis_combo.currentData()
        y_signal = self.y_axis_combo.currentData()
        self.xy_axes_changed.emit({
            'x': x_signal,
            'y': y_signal
        })
    
    def get_graph_count(self) -> int:
        """Get current graph count setting."""
        return self.graph_count_spinbox.value()
    
    def set_graph_count(self, count: int):
        """
        Set graph count value.
        
        Args:
            count: Graph count (1-10)
        """
        if 1 <= count <= 10:
            self.graph_count_spinbox.setValue(count)

    def is_overlay_mode_enabled(self) -> bool:
        """Return whether overlay mode is enabled."""
        return self.overlay_checkbox.isChecked()

    def set_overlay_mode(self, enabled: bool):
        """Set overlay mode checkbox state."""
        self.overlay_checkbox.setChecked(enabled)

    def is_xy_mode_enabled(self) -> bool:
        """Return whether XY mode is enabled."""
        return self.xy_mode_checkbox.isChecked()

    def set_xy_mode(self, enabled: bool):
        """Set XY mode checkbox state."""
        self.xy_mode_checkbox.setChecked(enabled)

    def get_xy_axis_selection(self) -> Dict[str, Optional[Dict[str, str]]]:
        """Return selected X and Y signals for XY plotting."""
        return {
            'x': self.x_axis_combo.currentData(),
            'y': self.y_axis_combo.currentData()
        }
