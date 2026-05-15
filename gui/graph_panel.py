"""
Graph Panel Widget
Right panel with dynamic number of synchronized graphs for signal visualization.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np
from typing import List, Dict, Tuple, Optional


class GraphPanel(QWidget):
    """Widget containing dynamically adjustable number of synchronized graphs."""
    
    def __init__(self, max_graphs: int = 5, colors: List[str] = None):
        super().__init__()
        self.max_graphs = max_graphs
        self.colors = colors if colors else [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        self.current_graph_count = 1  # Default to 1 graph
        self.plot_widgets: List[Optional[pg.PlotWidget]] = []
        self.plot_items: List[List[pg.PlotDataItem]] = []
        self.signal_info: List[List[Dict]] = []
        self.signal_data: List[List[Dict]] = []  # Store signal data for re-plotting
        self.secondary_viewboxes: List[Optional[pg.ViewBox]] = []  # for right-side axes
        self.splitter = None
        self.is_dark_mode = False
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for resizable graphs
        self.splitter = QSplitter(Qt.Vertical)
        
        # Create initial graph(s) based on current_graph_count
        self._create_graphs(self.current_graph_count)
        
        self.layout.addWidget(self.splitter)
        self.setLayout(self.layout)
    
    def _create_graphs(self, count: int):
        """
        Create the specified number of graphs.
        
        Args:
            count: Number of graphs to create
        """
        # Clear existing graphs
        for widget in self.plot_widgets:
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        
        self.plot_widgets.clear()
        self.plot_items.clear()
        self.signal_info.clear()
        self.signal_data.clear()
        self.secondary_viewboxes.clear()
        
        # Create new graphs
        for i in range(count):
            plot_widget = self._create_single_plot(i)
            self.plot_widgets.append(plot_widget)
            self.plot_items.append([])
            self.signal_info.append([])
            self.signal_data.append([])
            self.secondary_viewboxes.append(None)
            self.splitter.addWidget(plot_widget)
    
    def _create_single_plot(self, index: int) -> pg.PlotWidget:
        """
        Create a single plot widget.
        
        Args:
            index: Index of the plot
            
        Returns:
            Configured PlotWidget
        """
        plot_widget = pg.PlotWidget()
        
        # Apply theme
        bg_color = '#1a1a1a' if self.is_dark_mode else 'w'
        fg_color = '#ffffff' if self.is_dark_mode else '#000000'
        
        plot_widget.setBackground(bg_color)
        plot_widget.showGrid(x=True, y=True, alpha=0.3)
        plot_widget.setLabel('left', 'Value', color=fg_color)
        plot_widget.setLabel('bottom', 'Time', units='s', color=fg_color)
        plot_widget.addLegend()
        
        # Enable mouse interaction and zoom
        plot_widget.setMouseEnabled(x=True, y=True)
        
        # Enable auto-range on Y axis
        plot_widget.enableAutoRange(axis='y', enable=True)
        
        # Link X axis to first plot for synchronization
        if index > 0 and self.plot_widgets:
            plot_widget.setXLink(self.plot_widgets[0])
        
        return plot_widget
    
    def set_graph_count(self, count: int):
        """
        Dynamically change the number of displayed graphs.
        
        Args:
            count: New number of graphs (1-10)
        """
        if count < 1 or count > 10:
            return
        
        if count == self.current_graph_count:
            return
        
        self.current_graph_count = count
        
        # Store current signal data before recreating graphs
        stored_data = []
        for i in range(len(self.signal_data)):
            if self.signal_data[i]:
                stored_data.append({
                    'items': [
                        {
                            'time': item['time'],
                            'value': item['value'],
                            'info': info
                        }
                        for item, info in zip(self.signal_data[i], self.signal_info[i])
                    ]
                })
        
        # Recreate graphs
        self._create_graphs(count)
        
        # Restore signal data to new graphs
        for i, data in enumerate(stored_data):
            if i < count:
                for item_index, item in enumerate(data['items']):
                    self.plot_signal(
                        i,
                        item['time'],
                        item['value'],
                        item['info'],
                        append=item_index > 0
                    )
    
    def set_theme(self, is_dark: bool):
        """
        Apply theme to all graphs.
        
        Args:
            is_dark: True for dark mode, False for light mode
        """
        self.is_dark_mode = is_dark
        
        # Update all plot widgets
        bg_color = '#1a1a1a' if is_dark else 'w'
        fg_color = '#ffffff' if is_dark else '#000000'
        
        for plot_widget in self.plot_widgets:
            if plot_widget:
                plot_widget.setBackground(bg_color)
                plot_widget.getAxis('left').setPen(fg_color)
                plot_widget.getAxis('bottom').setPen(fg_color)
                plot_widget.getAxis('left').setTextPen(fg_color)
                plot_widget.getAxis('bottom').setTextPen(fg_color)
                # update right axis if present
                try:
                    plot_widget.getAxis('right').setPen(fg_color)
                    plot_widget.getAxis('right').setTextPen(fg_color)
                except Exception:
                    pass

    def _ensure_right_axis(self, index: int) -> Optional[pg.ViewBox]:
        """
        Ensure a right-side ViewBox and axis exist for the specified plot index.
        Returns the secondary ViewBox.
        """
        if index >= len(self.plot_widgets):
            return None

        if self.secondary_viewboxes[index] is not None:
            return self.secondary_viewboxes[index]

        plot_widget = self.plot_widgets[index]
        plot_item = plot_widget.getPlotItem()

        # create secondary viewbox and link it to the right axis
        vb = pg.ViewBox()
        plot_item.scene().addItem(vb)
        plot_item.showAxis('right')
        plot_item.getAxis('right').linkToView(vb)
        plot_item.getAxis('right').setZValue(100)

        # keep the X range linked to the main plot widget's viewbox
        vb.setXLink(plot_item.vb)

        # update geometry when main viewbox is resized
        def update_vb():
            try:
                vb.setGeometry(plot_item.vb.sceneBoundingRect())
                vb.linkedViewChanged(plot_item.vb, plot_item.vb.XAxis)
            except Exception:
                pass

        plot_item.vb.sigResized.connect(update_vb)
        # perform initial update to position the right viewbox
        update_vb()

        # store secondary viewbox
        self.secondary_viewboxes[index] = vb
        return vb
    
    def plot_signal(
        self,
        index: int,
        time_data: np.ndarray,
        value_data: np.ndarray,
        signal_info: Dict[str, str],
        append: bool = False,
        y_axis: Optional[str] = None
    ):
        """
        Plot a signal on a specific graph.
        
        Args:
            index: Graph index
            time_data: Time values array
            value_data: Signal values array
            signal_info: Dictionary with signal metadata (message, signal, unit)
        """
        if index >= len(self.plot_widgets):
            return
        
        plot_widget = self.plot_widgets[index]
        
        if index >= len(self.plot_items):
            return

        # Clear previous plot unless we are overlaying on the same graph
        if not append:
            self.clear_graph(index)
        
        # Create new plot
        color_index = len(self.signal_info[index])
        color = self.colors[color_index % len(self.colors)]
        pen = pg.mkPen(color=color, width=2)
        
        label = f"{signal_info['message']}.{signal_info['signal']}"
        if signal_info['unit']:
            label += f" ({signal_info['unit']})"
        
        # Decide target axis: if unspecified and overlaying a second signal, use right axis
        target_axis = y_axis
        if target_axis is None and append and len(self.signal_info[index]) == 1:
            target_axis = 'right'
        if target_axis not in ('left', 'right'):
            target_axis = 'left'

        if target_axis == 'left':
            plot_item = plot_widget.plot(
                time_data,
                value_data,
                pen=pen,
                name=label
            )
        else:
            vb = self._ensure_right_axis(index)
            if vb is None:
                # fallback to left if right axis could not be created
                plot_item = plot_widget.plot(
                    time_data,
                    value_data,
                    pen=pen,
                    name=label
                )
            else:
                curve = pg.PlotDataItem(time_data, value_data, pen=pen, name=label)
                vb.addItem(curve)
                plot_item = curve
        
        # Store plot item and signal info
        self.plot_items[index].append(plot_item)
        self.signal_info[index].append(signal_info)
        self.signal_data[index].append({
                'time': time_data,
                'value': value_data
        })
        
        # Update axis label
        fg_color = '#ffffff' if self.is_dark_mode else '#000000'
        plot_widget.setLabel('bottom', 'Time', units='s', color=fg_color)
        if len(self.signal_info[index]) > 1:
            # If multiple signals, keep generic left label; right axis will show its own label
            y_label = 'Value'
        else:
            y_label = signal_info['signal']
            if signal_info['unit']:
                y_label += f" ({signal_info['unit']})"
        plot_widget.setLabel('left', y_label, color=fg_color)
        # set right axis label if the last plotted item went to right
        if target_axis == 'right':
            try:
                right_label = signal_info['signal']
                if signal_info.get('unit'):
                    right_label += f" ({signal_info['unit']})"
                plot_widget.setLabel('right', right_label, color=fg_color)
            except Exception:
                pass

    def set_axis_range(self, index: int, side: str, vmin: float, vmax: float):
        """
        Set Y-axis range for given graph and side ('left' or 'right').
        """
        if index >= len(self.plot_widgets):
            return
        plot_widget = self.plot_widgets[index]
        if side == 'left':
            plot_widget.setYRange(vmin, vmax, padding=0)
        elif side == 'right':
            vb = None
            if index < len(self.secondary_viewboxes):
                vb = self.secondary_viewboxes[index]
            if vb is not None:
                vb.setYRange(vmin, vmax, padding=0)

    def enable_axis_autorange(self, index: int, side: str, enable: bool = True):
        """
        Enable or disable auto-range for the specified Y axis.
        """
        if index >= len(self.plot_widgets):
            return
        plot_widget = self.plot_widgets[index]
        if side == 'left':
            plot_widget.enableAutoRange(axis='y', enable=enable)
        elif side == 'right':
            vb = None
            if index < len(self.secondary_viewboxes):
                vb = self.secondary_viewboxes[index]
            if vb is not None:
                if enable:
                    vb.enableAutoRange(axis='y', enable=True)
                else:
                    vb.enableAutoRange(axis='y', enable=False)

    def plot_xy_relation(
        self,
        index: int,
        x_data: np.ndarray,
        y_data: np.ndarray,
        x_info: Dict[str, str],
        y_info: Dict[str, str],
        append: bool = False
    ):
        """Plot a synchronized X-Y relation on a specific graph."""
        if index >= len(self.plot_widgets):
            return

        plot_widget = self.plot_widgets[index]
        if index >= len(self.plot_items):
            return

        if not append:
            self.clear_graph(index)

        color_index = len(self.signal_info[index])
        color = self.colors[color_index % len(self.colors)]
        pen = pg.mkPen(color=color, width=2)

        x_name = f"{x_info['message']}.{x_info['signal']}"
        y_name = f"{y_info['message']}.{y_info['signal']}"
        label = f"{y_name} vs {x_name}"

        plot_item = plot_widget.plot(
            x_data,
            y_data,
            pen=pen,
            name=label
        )

        self.plot_items[index].append(plot_item)
        self.signal_info[index].append({
            'message': y_info['message'],
            'signal': y_info['signal'],
            'unit': y_info.get('unit', ''),
            'x_signal': x_name,
            'plot_type': 'xy'
        })
        self.signal_data[index].append({
            'time': x_data,
            'value': y_data,
            'x_data': x_data,
            'y_data': y_data,
            'plot_type': 'xy'
        })

        fg_color = '#ffffff' if self.is_dark_mode else '#000000'
        x_axis = x_info['signal']
        if x_info.get('unit'):
            x_axis += f" ({x_info['unit']})"
        y_axis = y_info['signal']
        if y_info.get('unit'):
            y_axis += f" ({y_info['unit']})"

        plot_widget.setLabel('bottom', x_axis, color=fg_color)
        plot_widget.setLabel('left', y_axis, color=fg_color)
    
    def clear_graph(self, index: int):
        """
        Clear a specific graph.
        
        Args:
            index: Graph index
        """
        if index >= len(self.plot_widgets):
            return
        
        plot_widget = self.plot_widgets[index]
        
        if index < len(self.plot_items):
            for item in self.plot_items[index]:
                plot_widget.removeItem(item)
            self.plot_items[index] = []
        
        if index < len(self.signal_info):
            self.signal_info[index] = []
        if index < len(self.signal_data):
            self.signal_data[index] = []

        # remove secondary viewbox/right axis if present
        if index < len(self.secondary_viewboxes):
            vb = self.secondary_viewboxes[index]
            if vb is not None:
                try:
                    plot_widget.getPlotItem().scene().removeItem(vb)
                except Exception:
                    try:
                        vb.setParent(None)
                    except Exception:
                        pass
                self.secondary_viewboxes[index] = None

        fg_color = '#ffffff' if self.is_dark_mode else '#000000'
        plot_widget.setLabel('left', 'Value', color=fg_color)
        try:
            plot_widget.setLabel('right', '', color=fg_color)
        except Exception:
            pass
    
    def clear_all(self):
        """Clear all graphs."""
        for i in range(len(self.plot_widgets)):
            self.clear_graph(i)
    
    def reset_zoom(self):
        """Reset zoom to show all data."""
        for plot_widget in self.plot_widgets:
            plot_widget.autoRange()
    
    def fit_to_data(self):
        """Fit view to data range (alias for reset_zoom)."""
        self.reset_zoom()
    
    def get_view_range(self) -> Dict[str, float]:
        """
        Get the current view range of the first plot.
        
        Returns:
            Dictionary with x_min and x_max
        """
        if self.plot_widgets:
            view_range = self.plot_widgets[0].viewRange()
            return {
                'x_min': view_range[0][0],
                'x_max': view_range[0][1]
            }
        return {'x_min': 0, 'x_max': 100}
    
    def set_view_range(self, x_min: float, x_max: float):
        """
        Set the view range for all plots.
        
        Args:
            x_min: Minimum X value
            x_max: Maximum X value
        """
        for plot_widget in self.plot_widgets:
            plot_widget.setXRange(x_min, x_max, padding=0)
    
    def export_graph(self, index: int, filepath: str) -> bool:
        """
        Export a specific graph to file.
        
        Args:
            index: Graph index
            filepath: Path to save the image
            
        Returns:
            True if successful
        """
        if index >= len(self.plot_widgets):
            return False
        
        from utils.export import GraphExporter
        return GraphExporter.export_graph(self.plot_widgets[index], filepath)
    
    def export_all(self, base_filepath: str) -> bool:
        """
        Export all graphs to separate files.
        
        Args:
            base_filepath: Base filepath for exports
            
        Returns:
            True if successful
        """
        from utils.export import GraphExporter
        return GraphExporter.export_all_graphs(self.plot_widgets, base_filepath)
    
    def get_current_graph_count(self) -> int:
        """Get the current number of graphs."""
        return self.current_graph_count
    
    def get_signal_data(self) -> Dict[str, Dict]:
        """
        Get all signal data currently displayed.
        
        Returns:
            Dictionary with signal data for statistics calculations
        """
        result = {}
        for graph_index, graph_signals in enumerate(self.signal_info):
            if graph_index >= len(self.signal_data):
                continue

            for signal_index, info in enumerate(graph_signals):
                if signal_index >= len(self.signal_data[graph_index]):
                    continue

                signal_data = self.signal_data[graph_index][signal_index]
                if not signal_data:
                    continue

                key = f"{info['message']}.{info['signal']}"
                unique_key = key
                suffix = 2
                while unique_key in result:
                    unique_key = f"{key} ({suffix})"
                    suffix += 1

                result[unique_key] = {
                    'time': signal_data['time'],
                    'value': signal_data['value'],
                    'unit': info.get('unit', ''),
                    'message': info['message'],
                    'signal': info['signal']
                }
        return result
