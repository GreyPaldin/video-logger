#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
import cv2
import numpy as np

class VideoWidget(QLabel):
    """Виджет для отображения видео с масштабированием"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 480)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("border: 2px solid gray; background-color: #333;")
        self.current_frame = None
    
    def update_frame(self, frame):
        """Обновить отображаемый кадр"""
        if frame is None:
            return
        
        self.current_frame = frame
        self._display_frame(frame)
    
    def _display_frame(self, frame):
        """Масштабировать и отобразить кадр"""
        h, w = frame.shape[:2]
        label_w = self.width()
        label_h = self.height()
        
        if label_w > 0 and label_h > 0:
            scale = min(label_w / w, label_h / h)
            new_w, new_h = int(w * scale), int(h * scale)
            
            if new_w > 0 and new_h > 0:
                resized = cv2.resize(frame, (new_w, new_h))
                rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                bytes_per_line = ch * w
                qt_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.setPixmap(QPixmap.fromImage(qt_img))
    
    def resizeEvent(self, event):
        """При изменении размера окна перерисовываем"""
        if self.current_frame is not None:
            self._display_frame(self.current_frame)
        super().resizeEvent(event)