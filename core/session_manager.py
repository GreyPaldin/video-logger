#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

class SessionManager:
    """
    Управление сессией записи:
    - Абсолютное время от старта
    - Привязка логов к видео
    - Координация между видео и логами
    """
    
    def __init__(self, video_recorder, data_logger):
        self.video_recorder = video_recorder
        self.data_logger = data_logger
        
        self.is_active = False
        self.session_start_time = None
        self.current_abs_time = 0.0
        
        # Колбэки для GUI
        self.on_data_callback = None      # новые данные с датчиков
        self.on_rotation_callback = None  # разбиение файла
    
    def start_session(self):
        """Начать сессию (кнопка Старт)"""
        self.is_active = True
        self.session_start_time = time.time()
        self.current_abs_time = 0.0
        
        # Запускаем видео
        self.video_recorder.start_recording()
        
        # Запускаем логирование
        self.data_logger.start_session(self.session_start_time)
        self.data_logger.set_video_active(True)
    
    def stop_session(self):
        """Остановить сессию (кнопка Стоп)"""
        self.is_active = False
        
        # Останавливаем видео
        self.video_recorder.stop_recording()
        
        # Останавливаем логирование
        self.data_logger.stop_session()
    
    def update_time(self):
        """Обновить текущее абсолютное время (вызывается по таймеру)"""
        if self.is_active and self.session_start_time:
            self.current_abs_time = time.time() - self.session_start_time
    
    def process_sensor_data(self, sensor_data):
        """
        Обработать полученные данные с МК:
        - Добавить временные метки
        - Передать в логгер
        - Отправить в GUI для отображения
        """
        if not self.is_active:
            return
        
        # Добавляем временные метки
        sensor_data.time_abs = self.current_abs_time
        
        if self.data_logger.current_file_start_time:
            sensor_data.time_file = time.time() - self.data_logger.current_file_start_time
        else:
            sensor_data.time_file = 0
        
        # Передаём в логгер
        self.data_logger.add_data(sensor_data)
        
        # Передаём в GUI для отображения
        if self.on_data_callback:
            self.on_data_callback(sensor_data)
    
    def on_video_frame(self, frame):
        """Обработка кадра видео (вызывается из VideoManager)"""
        if not self.is_active:
            return
        
        # Записываем кадр
        rotated = self.video_recorder.write_frame(frame)
        
        # Если произошло разбиение видео, уведомляем логгер
        if rotated:
            self.data_logger.check_rotation(0)
            if self.on_rotation_callback:
                self.on_rotation_callback(self.video_recorder.current_part_index - 1)