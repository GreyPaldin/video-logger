#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
from pathlib import Path

# Заголовок CSV с разделителем ;
CSV_HEADER = "time_abs_sec;time_file_sec;encoder_deg;pitch_deg;roll_deg;Ax_ms2;Ay_ms2;Az_ms2;Gx_dps;Gy_dps;Gz_dps;gps_fix;lat_deg;lon_deg;alt_m;speed_ms\n"

class DataLogger:
    def __init__(self, config_manager):
        self.config = config_manager
        self.buffer = []
        self.current_file = None
        self.current_file_start_time = None
        self.current_part_index = 1
        self.is_logging = False
        self.video_active = False
        self.session_start_time = None
    
    def start_session(self, session_start_time):
        self.session_start_time = session_start_time
        self.current_part_index = 1
        self.is_logging = True
        self.buffer = []
        self.video_active = False
    
    def stop_session(self):
        if self.is_logging:
            self.flush()
            if self.current_file:
                self._close_files()
        self.is_logging = False
    
    def set_video_active(self, active):
        self.video_active = active
        if active and not self.current_file:
            self._start_new_log_file()
        elif not active and self.current_file:
            self.flush()
            self._close_files()
            self.current_part_index = 1
    
    def add_data(self, sensor_data):
        if not self.is_logging:
            return
        if not self.current_file:
            self._start_new_log_file()
        self.buffer.append(sensor_data)
        if len(self.buffer) >= 100:
            self.flush()
    
    def flush(self):
        if not self.buffer:
            return
        if not self.current_file:
            self._start_new_log_file()
        format_type = self.config.get('logging', 'format')
        for data in self.buffer:
            # Превращаем в строку с разделителем ;
            line = self._sensor_data_to_csv_line(data)
            if format_type in ['csv', 'both']:
                self.current_file['csv'].write(line)
                self.current_file['csv'].flush()
            if format_type in ['json', 'both']:
                self.current_file['json'].write(json.dumps(data.to_dict()) + '\n')
                self.current_file['json'].flush()
        self.buffer = []
    
    def _sensor_data_to_csv_line(self, data):
        """Форматирует строку CSV с разделителем ;"""
        d = data.to_dict()
        return f"{d['time_abs_sec']};{d['time_file_sec']};{d['encoder_deg']};{d['pitch_deg']};{d['roll_deg']};{d['Ax_ms2']};{d['Ay_ms2']};{d['Az_ms2']};{d['Gx_dps']};{d['Gy_dps']};{d['Gz_dps']};{d['gps_fix']};{d['lat_deg']};{d['lon_deg']};{d['alt_m']};{d['speed_ms']}\n"
    
    def check_rotation(self, current_video_duration):
        segment_duration = self.config.get('video', 'segment_duration_sec')
        if self.current_file and self.current_file_start_time:
            elapsed = time.time() - self.current_file_start_time
            if elapsed >= segment_duration:
                self._start_new_log_file()
                return True
        return False
    
    def _start_new_log_file(self):
        if self.current_file:
            self.flush()
            self._close_files()
        
        if self.video_active:
            base_name = f"video_{self._get_timestamp()}_{self.current_part_index:03d}"
        else:
            base_name = f"log_no_video_{self._get_timestamp()}_{self.current_part_index:03d}"
        
        log_folder = Path(self.config.get('logging', 'log_folder'))
        log_folder.mkdir(parents=True, exist_ok=True)
        format_type = self.config.get('logging', 'format')
        self.current_file = {}
        
        if format_type in ['csv', 'both']:
            csv_path = log_folder / f"{base_name}.csv"
            f = open(csv_path, 'w', encoding='utf-8-sig')  # BOM для Excel
            f.write(CSV_HEADER)
            self.current_file['csv'] = f
        
        if format_type in ['json', 'both']:
            json_path = log_folder / f"{base_name}.json"
            self.current_file['json'] = open(json_path, 'w')
        
        self.current_part_index += 1
        self.current_file_start_time = time.time()
    
    def _close_files(self):
        if self.current_file:
            if 'csv' in self.current_file:
                self.current_file['csv'].close()
            if 'json' in self.current_file:
                self.current_file['json'].close()
            self.current_file = None
    
    def _get_timestamp(self):
        return time.strftime("%Y%m%d_%H%M%S")