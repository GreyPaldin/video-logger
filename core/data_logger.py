#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
from pathlib import Path
from models.sensor_data import CSV_HEADER

class DataLogger:
    """
    Логирование данных с буфером 100 пакетов.
    Привязка к видео: новый лог-файл при старте нового видеофайла.
    """
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.buffer = []  # буфер пакетов
        self.current_file = None
        self.current_file_start_time = None
        self.current_part_index = 1
        self.is_logging = False
        self.video_active = False
        self.session_start_time = None
    
    def start_session(self, session_start_time):
        """Начать новую сессию (при нажатии Старт)"""
        self.session_start_time = session_start_time
        self.current_part_index = 1
        self.is_logging = True
        self.buffer = []
        self.video_active = False
    
    def stop_session(self):
        """Остановить сессию (при нажатии Стоп)"""
        if self.is_logging:
            self.flush()
            if self.current_file:
                self._close_files()
        self.is_logging = False
    
    def set_video_active(self, active):
        """Установить флаг активности видео (для привязки логов)"""
        self.video_active = active
        if active and not self.current_file:
            self._start_new_log_file()
        elif not active and self.current_file:
            self.flush()
            self._close_files()
            self.current_part_index = 1
    
    def add_data(self, sensor_data):
        """Добавить пакет данных в буфер"""
        if not self.is_logging:
            return
        
        # Если нет активного лог-файла, создаём
        if not self.current_file:
            self._start_new_log_file()
        
        # Добавляем в буфер
        self.buffer.append(sensor_data)
        
        # Если набрали 100 пакетов — сбрасываем на диск
        if len(self.buffer) >= 100:
            self.flush()
    
    def flush(self):
        """Сбросить буфер на диск"""
        if not self.buffer:
            return
        
        if not self.current_file:
            self._start_new_log_file()
        
        format_type = self.config.get('logging', 'format')
        
        for data in self.buffer:
            if format_type in ['csv', 'both']:
                self.current_file['csv'].write(data.to_csv_line())
                self.current_file['csv'].flush()
            
            if format_type in ['json', 'both']:
                self.current_file['json'].write(json.dumps(data.to_dict()) + '\n')
                self.current_file['json'].flush()
        
        self.buffer = []
    
    def check_rotation(self, current_video_duration):
        """
        Проверить, нужно ли создать новый лог-файл (при разбиении видео)
        Вызывается из session_manager при разбиении видео
        """
        segment_duration = self.config.get('video', 'segment_duration_sec')
        
        if self.current_file and self.current_file_start_time:
            elapsed = time.time() - self.current_file_start_time
            if elapsed >= segment_duration:
                self._start_new_log_file()
                return True
        return False
    
    def _start_new_log_file(self):
        """Создать новый лог-файл (при разбиении или старте)"""
        # Закрываем старый файл, если есть
        if self.current_file:
            self.flush()
            self._close_files()
        
        # Определяем базовое имя файла
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
            f = open(csv_path, 'w')
            f.write(CSV_HEADER)
            self.current_file['csv'] = f
        
        if format_type in ['json', 'both']:
            json_path = log_folder / f"{base_name}.json"
            self.current_file['json'] = open(json_path, 'w')
        
        self.current_part_index += 1
        self.current_file_start_time = time.time()
    
    def _close_files(self):
        """Закрыть текущие файлы"""
        if self.current_file:
            if 'csv' in self.current_file:
                self.current_file['csv'].close()
            if 'json' in self.current_file:
                self.current_file['json'].close()
            self.current_file = None
    
    def _get_timestamp(self):
        """Получить временную метку для имени файла"""
        return time.strftime("%Y%m%d_%H%M%S")