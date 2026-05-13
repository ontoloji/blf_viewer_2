"""
Statistics Widget Module
Displays statistics for data between two cursors.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt5.QtCore import Qt
import numpy as np
from typing import Dict


class StatisticsWidget(QWidget):
    """Widget for displaying cursor-based statistics."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create scroll area for statistics
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Create label for statistics content
        self.stats_label = QLabel("No cursors active")
        self.stats_label.setWordWrap(True)
        self.stats_label.setTextFormat(Qt.RichText)
        self.stats_label.setAlignment(Qt.AlignTop)
        self.stats_label.setStyleSheet("padding: 5px;")
        
        scroll_area.setWidget(self.stats_label)
        layout.addWidget(scroll_area)
        
        self.setLayout(layout)
    
    def update_statistics(self, cursor_positions: Dict[int, float], 
                         signal_data_dict: Dict[str, Dict]):
        """
        Update statistics display based on cursor positions.
        
        Args:
            cursor_positions: Dictionary mapping cursor_id to time position
            signal_data_dict: Dictionary with signal data
                Format: {
                    'signal_name': {
                        'time': np.ndarray,
                        'value': np.ndarray,
                        'unit': str,
                        'message': str,
                        'signal': str
                    }
                }
        """
        if len(cursor_positions) == 0:
            self.stats_label.setText(
                "<h3>Cursor Statistics</h3>"
                "<p style='color: gray;'><i>No cursors active</i></p>"
            )
            return

        # Single-cursor mode: show interpolated values at that cursor
        if len(cursor_positions) == 1:
            cursor_id, cursor_time = next(iter(cursor_positions.items()))

            html = "<h3>Cursor Statistics</h3>"
            html += f"<p><b>Cursor {cursor_id}:</b> {cursor_time:.3f}s</p>"
            html += "<hr>"

            if not signal_data_dict:
                html += "<p style='color: gray;'><i>No signals selected</i></p>"
                self.stats_label.setText(html)
                return

            for signal_key, data in signal_data_dict.items():
                if data is None or 'time' not in data or 'value' not in data:
                    continue

                time_array = data['time']
                value_array = data['value']

                # Interpolate value at cursor time
                cursor_value = self._interpolate_at_time(time_array, value_array, cursor_time)

                signal_name = data.get('signal', signal_key)
                message_name = data.get('message', '')
                unit = data.get('unit', '')

                if message_name:
                    full_name = f"{message_name}.{signal_name}"
                else:
                    full_name = signal_name

                html += f"<p><b>{full_name}</b>"
                if unit:
                    html += f" <span style='color: gray;'>({unit})</span>"
                html += "</p>"

                html += "<table style='margin-left: 15px; margin-bottom: 10px;'>"
                html += f"<tr><td>Cursor {cursor_id} Value:</td><td><b>{cursor_value:.3f}</b></td></tr>"
                html += "</table>"

            self.stats_label.setText(html)
            return
        
        cursor1_time = cursor_positions.get(1)
        cursor2_time = cursor_positions.get(2)

        if cursor1_time is None or cursor2_time is None:
            positions = sorted(cursor_positions.values())
            cursor1_time, cursor2_time = positions[0], positions[1]

        # Statistics are computed in the time interval between cursor positions
        t1, t2 = sorted([cursor1_time, cursor2_time])
        
        # Build HTML content
        html = "<h3>Cursor Statistics</h3>"
        html += f"<p><b>Cursor 1:</b> {cursor1_time:.3f}s</p>"
        html += f"<p><b>Cursor 2:</b> {cursor2_time:.3f}s</p>"
        html += f"<p><b>Time Range:</b> {t1:.3f}s to {t2:.3f}s</p>"
        html += f"<p><b>Duration:</b> Δt = {t2-t1:.3f}s</p>"
        html += "<hr>"
        
        if not signal_data_dict:
            html += "<p style='color: gray;'><i>No signals selected</i></p>"
            self.stats_label.setText(html)
            return
        
        # Calculate statistics for each signal
        for signal_key, data in signal_data_dict.items():
            if data is None or 'time' not in data or 'value' not in data:
                continue
            
            time_array = data['time']
            value_array = data['value']
            
            # Filter data within cursor range
            mask = (time_array >= t1) & (time_array <= t2)
            values_in_range = value_array[mask]
            
            if len(values_in_range) == 0:
                continue
            
            # Calculate statistics
            avg = np.mean(values_in_range)
            max_val = np.max(values_in_range)
            min_val = np.min(values_in_range)
            std_dev = np.std(values_in_range)
            cursor1_value = self._interpolate_at_time(time_array, value_array, cursor1_time)
            cursor2_value = self._interpolate_at_time(time_array, value_array, cursor2_time)
            
            # Get signal info
            signal_name = data.get('signal', signal_key)
            message_name = data.get('message', '')
            unit = data.get('unit', '')
            
            # Format signal name
            if message_name:
                full_name = f"{message_name}.{signal_name}"
            else:
                full_name = signal_name
            
            # Add to HTML
            html += f"<p><b>{full_name}</b>"
            if unit:
                html += f" <span style='color: gray;'>({unit})</span>"
            html += "</p>"
            
            html += "<table style='margin-left: 15px; margin-bottom: 10px;'>"
            html += f"<tr><td>Cursor 1 Value:</td><td><b>{cursor1_value:.3f}</b></td></tr>"
            html += f"<tr><td>Cursor 2 Value:</td><td><b>{cursor2_value:.3f}</b></td></tr>"
            html += f"<tr><td>Average:</td><td><b>{avg:.3f}</b></td></tr>"
            html += f"<tr><td>Maximum:</td><td><b>{max_val:.3f}</b></td></tr>"
            html += f"<tr><td>Minimum:</td><td><b>{min_val:.3f}</b></td></tr>"
            html += f"<tr><td>Std Dev:</td><td><b>{std_dev:.3f}</b></td></tr>"
            html += f"<tr><td>Samples:</td><td><b>{len(values_in_range)}</b></td></tr>"
            html += "</table>"
        
        self.stats_label.setText(html)

    def _interpolate_at_time(self, time_array: np.ndarray, value_array: np.ndarray, query_time: float) -> float:
        """Return interpolated signal value at the given time."""
        if len(time_array) == 0 or len(value_array) == 0:
            return float('nan')

        clamped_time = min(max(query_time, float(time_array[0])), float(time_array[-1]))
        return float(np.interp(clamped_time, time_array, value_array))
    
    def clear_statistics(self):
        """Clear the statistics display."""
        self.stats_label.setText(
            "<h3>Cursor Statistics</h3>"
            "<p style='color: gray;'><i>No cursors active</i></p>"
        )
