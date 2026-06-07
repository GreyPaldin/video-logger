#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import time
from core.platform_detector import IS_JETSON, IS_WINDOWS

class VideoCapture:
    """Захват видео с камеры (поддерживает USB на Windows и CSI на Jetson)"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.cap = None
        self.width = config_manager.get('video', 'width')
        self.height = config_manager.get('video', 'height')
        self.fps = config_manager.get('video', 'fps')
        self.camera_id = config_manager.get('video', 'camera_id')
    
    def apply_settings(self):
        """Применить настройки камеры"""
        self.width = self.config.get('video', 'width')
        self.height = self.config.get('video', 'height')
        self.fps = self.config.get('video', 'fps')
        self.camera_id = self.config.get('video', 'camera_id')
    
    def open(self):
        """Открыть камеру"""
        if self.cap:
            self.release()
        
        # Определяем тип камеры
        if IS_JETSON and self.camera_id.startswith("CSI"):
            sensor_id = int(self.camera_id.split()[-1])
            gst_str = (
                f"nvarguscamerasrc sensor-id={sensor_id} ! "
                f"video/x-raw(memory:NVMM), width={self.width}, height={self.height}, "
                f"framerate={self.fps}/1 ! "
                f"nvvidconv ! video/x-raw, format=BGRx ! "
                f"videoconvert ! video/x-raw, format=BGR ! "
                f"appsink"
            )
            self.cap = cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
        else:
            # Windows или USB камера
            cam_num = 0
            if self.camera_id.startswith("USB"):
                cam_num = int(self.camera_id.split()[-1])
            
            self.cap = cv2.VideoCapture(cam_num)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        return self.cap.isOpened()
    
    def read(self):
        """Прочитать кадр"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None
    
    def release(self):
        """Освободить камеру"""
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def get_available_cameras(self):
        """Поиск доступных камер (CSI и USB)"""
        cameras = []
        
        if IS_JETSON:
            # Проверяем CSI камеры Jetson
            for sensor_id in [0, 1]:
                test_gst = (
                    f"nvarguscamerasrc sensor-id={sensor_id} ! "
                    f"video/x-raw(memory:NVMM), width=640, height=480 ! "
                    f"nvvidconv ! video/x-raw, format=BGRx ! "
                    f"videoconvert ! video/x-raw, format=BGR ! "
                    f"fakesink"
                )
                test_cap = cv2.VideoCapture(test_gst, cv2.CAP_GSTREAMER)
                if test_cap.isOpened():
                    cameras.append(f"CSI Camera {sensor_id}")
                    test_cap.release()
        
        # Проверяем USB камеры
        for i in range(4):
            test_cap = cv2.VideoCapture(i)
            if test_cap.isOpened():
                cameras.append(f"USB Camera {i}")
                test_cap.release()
        
        return cameras if cameras else ["No camera found"]