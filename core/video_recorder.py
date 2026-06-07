#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import time
from pathlib import Path
from datetime import datetime
from core.platform_detector import IS_JETSON

class VideoRecorder:
    """Запись видео с автоматическим разбиением на файлы"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.video_writer = None
        self.current_file = None
        self.current_file_start_time = None
        self.current_part_index = 1
        self.is_recording = False
        self.frame_count = 0
        
        # Настройки
        self.apply_settings()
    
    def apply_settings(self):
        """Применить настройки из конфига"""
        self.width = self.config.get('video', 'width')
        self.height = self.config.get('video', 'height')
        self.fps = self.config.get('video', 'fps')
        self.bitrate = self.config.get('video', 'bitrate_mbps') * 1000000
        self.segment_duration = self.config.get('video', 'segment_duration_sec')
        self.video_folder = Path(self.config.get('video', 'video_folder'))
    
    def start_recording(self):
        """Начать запись (создать первый файл)"""
        self.is_recording = True
        self.current_part_index = 1
        self.frame_count = 0
        self._start_new_video_file()
        return True
    
    def stop_recording(self):
        """Остановить запись"""
        self.is_recording = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
    
    def write_frame(self, frame):
        """Записать один кадр"""
        if not self.is_recording or frame is None:
            return
        
        if self.video_writer:
            self.video_writer.write(frame)
            self.frame_count += 1
        
        # Проверка на разбиение файла
        if self.current_file_start_time:
            elapsed = time.time() - self.current_file_start_time
            if elapsed >= self.segment_duration:
                self._start_new_video_file()
                return True  # сигнал, что произошло разбиение
        return False
    
    def _start_new_video_file(self):
        """Создать новый видеофайл"""
        # Закрываем старый
        if self.video_writer:
            self.video_writer.release()
        
        self.video_folder.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.video_folder / f"video_{timestamp}_{self.current_part_index:03d}.mp4"
        
        # Создаём VideoWriter в зависимости от платформы
        if IS_JETSON:
            # GStreamer с аппаратным кодированием для Jetson
            out_gst = (
                f"appsrc ! videoconvert ! video/x-raw, format=BGRx ! "
                f"nvvidconv ! nvv4l2h264enc bitrate={self.bitrate} "
                f"insert-sps-pps=true ! "
                f"h264parse ! qtmux ! filesink location={str(filename)}"
            )
            self.video_writer = cv2.VideoWriter(
                out_gst,
                cv2.CAP_GSTREAMER,
                0,
                self.fps,
                (self.width, self.height)
            )
        else:
            # Windows: обычный MP4V кодек
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(
                str(filename),
                fourcc,
                self.fps,
                (self.width, self.height)
            )
        
        self.current_file = filename
        self.current_file_start_time = time.time()
        self.current_part_index += 1