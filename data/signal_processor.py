"""
Signal Processor Module
Handles signal decoding and processing for visualization.
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional


class SignalProcessor:
    """Class for processing and preparing CAN signals for visualization."""
    
    def __init__(self, blf_reader, dbc_parser):
        """
        Initialize the signal processor.
        
        Args:
            blf_reader: BLFReader instance
            dbc_parser: DBCParser instance
        """
        self.blf_reader = blf_reader
        self.dbc_parser = dbc_parser
        self.processed_signals: Dict[str, Dict[str, np.ndarray]] = {}
    
    def process_signal(self, message_name: str, signal_name: str) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Process a specific signal from BLF data using DBC definitions.
        
        Args:
            message_name: Name of the CAN message
            signal_name: Name of the signal within the message
            
        Returns:
            Tuple of (timestamps, values) as numpy arrays, or None if processing fails
        """
        # Get message definition from DBC
        message = self.dbc_parser.get_message_by_name(message_name)
        if not message:
            print(f"Message '{message_name}' not found in DBC")
            return None
        
        # Get all messages with this ID from BLF
        blf_messages = self.blf_reader.get_messages_by_id(message.frame_id)
        if not blf_messages:
            print(f"No messages with ID {message.frame_id} found in BLF")
            return None
        
        timestamps = []
        values = []
        
        # Decode each message and extract the signal
        debug_count = 0
        for msg in blf_messages:
            try:
                decoded = self.dbc_parser.decode_message(message.frame_id, msg['data'])
                if decoded and signal_name in decoded:
                    value = decoded[signal_name]
                    
                    # DEBUG: İlk 3 mesajda kontrol et
                    if debug_count < 3:
                        signal_obj = None
                        for sig in message.signals:
                            if sig.name == signal_name:
                                signal_obj = sig
                                break
                        
                        if signal_obj:
                            print(f"\n=== DEBUG: {signal_name} ===")
                            print(f"Raw value from decode: {value}")
                            print(f"Scale: {signal_obj.scale}")
                            print(f"Offset: {signal_obj.offset}")
                            print(f"Expected: {(value * signal_obj.scale) + signal_obj.offset}")
                        
                        debug_count += 1
                    
                    timestamps.append(msg['timestamp'])
                    values.append(value)
            except Exception as e:
                # Skip messages that fail to decode
                continue
        
        if not timestamps:
            print(f"No valid data for signal '{signal_name}' in message '{message_name}'")
            return None
        
        # Convert to numpy arrays
        time_array = np.array(timestamps)
        value_array = np.array(values)
        
        # Cache the processed signal
        key = f"{message_name}.{signal_name}"
        self.processed_signals[key] = {
            'time': time_array,
            'value': value_array
        }
        
        return time_array, value_array
    
    def get_signal_info(self, message_name: str, signal_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a signal.
        
        Args:
            message_name: Name of the CAN message
            signal_name: Name of the signal
            
        Returns:
            Dictionary with signal information or None
        """
        message = self.dbc_parser.get_message_by_name(message_name)
        if not message:
            return None
        
        for signal in message.signals:
            if signal.name == signal_name:
                return {
                    'name': signal.name,
                    'unit': signal.unit if signal.unit else '',
                    'min': signal.minimum,
                    'max': signal.maximum,
                    'scale': signal.scale,
                    'offset': signal.offset
                }
        
        return None
    
    def get_cached_signal(self, message_name: str, signal_name: str) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Get a previously processed signal from cache.
        
        Args:
            message_name: Name of the CAN message
            signal_name: Name of the signal
            
        Returns:
            Tuple of (timestamps, values) or None if not cached
        """
        key = f"{message_name}.{signal_name}"
        if key in self.processed_signals:
            data = self.processed_signals[key]
            return data['time'], data['value']
        return None
    
    def clear_cache(self):
        """Clear all cached processed signals."""
        self.processed_signals.clear()

    def _prepare_series(
        self,
        time_data: np.ndarray,
        value_data: np.ndarray,
        time_range: Optional[Tuple[float, float]] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Sort a series by time, drop duplicate timestamps, and optionally crop by range.
        """
        if len(time_data) == 0 or len(value_data) == 0:
            return np.array([]), np.array([])

        order = np.argsort(time_data)
        t_sorted = np.asarray(time_data[order], dtype=float)
        v_sorted = np.asarray(value_data[order], dtype=float)

        # Keep the last value for duplicate timestamps.
        if len(t_sorted) > 1:
            keep = np.ones(len(t_sorted), dtype=bool)
            keep[:-1] = t_sorted[:-1] != t_sorted[1:]
            t_sorted = t_sorted[keep]
            v_sorted = v_sorted[keep]

        if time_range is not None and len(t_sorted) > 0:
            t_min, t_max = sorted(time_range)
            mask = (t_sorted >= t_min) & (t_sorted <= t_max)
            t_sorted = t_sorted[mask]
            v_sorted = v_sorted[mask]

        return t_sorted, v_sorted

    def _interpolate_values(
        self,
        source_time: np.ndarray,
        source_value: np.ndarray,
        target_time: np.ndarray,
        method: str = 'linear'
    ) -> np.ndarray:
        """Interpolate source values at target timestamps."""
        if len(source_time) == 0 or len(source_value) == 0 or len(target_time) == 0:
            return np.array([])

        if method == 'nearest':
            indices = np.searchsorted(source_time, target_time, side='left')
            indices = np.clip(indices, 0, len(source_time) - 1)
            left = np.clip(indices - 1, 0, len(source_time) - 1)
            right = indices
            choose_left = np.abs(target_time - source_time[left]) <= np.abs(source_time[right] - target_time)
            nearest_idx = np.where(choose_left, left, right)
            return source_value[nearest_idx]

        clipped_target = np.clip(target_time, float(source_time[0]), float(source_time[-1]))
        return np.interp(clipped_target, source_time, source_value)

    def thin_xy_data(
        self,
        x_data: np.ndarray,
        y_data: np.ndarray,
        max_points: int = 5000,
        return_indices: bool = False
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Reduce plotted point count while preserving major shape changes.

        Uses min-max sampling per bucket on Y while preserving original order.
        """
        count = min(len(x_data), len(y_data))
        if count <= max_points:
            if return_indices:
                return x_data, y_data, np.arange(count, dtype=int)
            return x_data, y_data

        if max_points < 10:
            max_points = 10

        bucket_count = max_points // 2
        bucket_size = int(np.ceil(count / bucket_count))
        keep_indices = {0, count - 1}

        for start in range(0, count, bucket_size):
            end = min(start + bucket_size, count)
            if end - start <= 0:
                continue

            y_bucket = y_data[start:end]
            local_min = int(np.argmin(y_bucket)) + start
            local_max = int(np.argmax(y_bucket)) + start
            keep_indices.add(local_min)
            keep_indices.add(local_max)

        ordered = np.array(sorted(keep_indices), dtype=int)
        if return_indices:
            return x_data[ordered], y_data[ordered], ordered
        return x_data[ordered], y_data[ordered]

    def create_xy_relation(
        self,
        x_message: str,
        x_signal: str,
        y_message: str,
        y_signal: str,
        time_range: Optional[Tuple[float, float]] = None,
        interpolation: str = 'linear',
        base: str = 'higher_rate',
        max_points: Optional[int] = 5000
    ) -> Optional[Dict[str, np.ndarray]]:
        """
        Build an X-Y relation by synchronizing two time-series signals.

        Args:
            x_message: Message name for X axis signal
            x_signal: Signal name for X axis
            y_message: Message name for Y axis signal
            y_signal: Signal name for Y axis
            time_range: Optional (start_time, end_time) filter
            interpolation: 'linear' or 'nearest'
            base: 'x', 'y', or 'higher_rate'
            max_points: Optional thinning limit for plotting

        Returns:
            Dict with aligned arrays or None if alignment fails.
        """
        x_series = self.get_cached_signal(x_message, x_signal) or self.process_signal(x_message, x_signal)
        y_series = self.get_cached_signal(y_message, y_signal) or self.process_signal(y_message, y_signal)

        if x_series is None or y_series is None:
            return None

        x_time_raw, x_value_raw = x_series
        y_time_raw, y_value_raw = y_series

        x_time, x_value = self._prepare_series(x_time_raw, x_value_raw, time_range)
        y_time, y_value = self._prepare_series(y_time_raw, y_value_raw, time_range)

        if len(x_time) < 2 or len(y_time) < 2:
            return None

        overlap_start = max(float(x_time[0]), float(y_time[0]))
        overlap_end = min(float(x_time[-1]), float(y_time[-1]))
        if overlap_start >= overlap_end:
            return None

        x_mask = (x_time >= overlap_start) & (x_time <= overlap_end)
        y_mask = (y_time >= overlap_start) & (y_time <= overlap_end)
        x_time = x_time[x_mask]
        x_value = x_value[x_mask]
        y_time = y_time[y_mask]
        y_value = y_value[y_mask]

        if len(x_time) < 2 or len(y_time) < 2:
            return None

        base_mode = base.lower()
        if base_mode not in {'x', 'y', 'higher_rate'}:
            base_mode = 'higher_rate'

        if base_mode == 'x':
            aligned_time = x_time
            x_aligned = x_value
            y_aligned = self._interpolate_values(y_time, y_value, aligned_time, interpolation)
        elif base_mode == 'y':
            aligned_time = y_time
            y_aligned = y_value
            x_aligned = self._interpolate_values(x_time, x_value, aligned_time, interpolation)
        else:
            use_x_as_base = len(x_time) >= len(y_time)
            if use_x_as_base:
                aligned_time = x_time
                x_aligned = x_value
                y_aligned = self._interpolate_values(y_time, y_value, aligned_time, interpolation)
            else:
                aligned_time = y_time
                y_aligned = y_value
                x_aligned = self._interpolate_values(x_time, x_value, aligned_time, interpolation)

        if len(x_aligned) == 0 or len(y_aligned) == 0:
            return None

        if max_points is not None and max_points > 0:
            x_aligned, y_aligned, kept_idx = self.thin_xy_data(
                x_aligned,
                y_aligned,
                max_points=max_points,
                return_indices=True
            )
            aligned_time = aligned_time[kept_idx]

        return {
            'x': x_aligned,
            'y': y_aligned,
            'time': aligned_time[:len(x_aligned)]
        }