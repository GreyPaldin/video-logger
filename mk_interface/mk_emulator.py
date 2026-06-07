#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import threading
import math
import random
from models.sensor_data import SensorData

class MKEmulator:
    """
    Эмулятор микроконтроллера для отладки.
    Генерирует фейковые данные датчиков с заданной частотой.
    """
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.data_callback = None
        self.status_callback = None
        
        self.is_running = False
        self.thread = None
        self.poll_hz = config_manager.get('protocol', 'poll_hz')
        
        # Для плавного изменения данных
        self.start_time = 0
        self.last_encoder = 0
    
    def set_poll_hz(self, hz):
        self.poll_hz = hz
    
    def start(self):
        """Запустить эмуляцию"""
        if self.is_running:
            return
        
        self.is_running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._emulation_loop)
        self.thread.daemon = True
        self.thread.start()
        
        if self.status_callback:
            self.status_callback(True)
    
    def stop(self):
        """Остановить эмуляцию"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1)
    
    def _emulation_loop(self):
        """Основной цикл генерации данных"""
        interval = 1.0 / self.poll_hz if self.poll_hz > 0 else 0.033
        
        while self.is_running:
            t = time.time() - self.start_time
            
            sd = SensorData()
            
            # Энкодер: вращение с ускорением/замедлением
            sd.encoder_deg = (t * 30) % 360  # 30 град/сек, зациклено
            
            # Углы pitch и roll: синусоидальные колебания
            sd.pitch_deg = 15 * math.sin(t * 0.5) + random.uniform(-0.5, 0.5)
            sd.roll_deg = 10 * math.sin(t * 0.7) + random.uniform(-0.5, 0.5)
            
            # Ускорения (с небольшим шумом)
            sd.ax_ms2 = 0.2 * math.sin(t * 1.2) + random.uniform(-0.1, 0.1)
            sd.ay_ms2 = 0.1 * math.cos(t * 1.1) + random.uniform(-0.1, 0.1)
            sd.az_ms2 = 9.81 + 0.5 * math.sin(t * 0.8) + random.uniform(-0.2, 0.2)
            
            # Угловые скорости
            sd.gx_dps = 30 * math.sin(t * 2) + random.uniform(-2, 2)
            sd.gy_dps = 20 * math.cos(t * 1.8) + random.uniform(-2, 2)
            sd.gz_dps = 15 * math.sin(t * 1.5) + random.uniform(-2, 2)
            
            # GPS: fix включается/выключается каждые 20 секунд
            fix_state = 2 if (int(t) % 20) < 15 else 0
            sd.gps_fix = fix_state
            
            # GPS координаты: плавное перемещение (имитация движения)
            sd.lat_deg = 55.7512 + 0.0005 * math.sin(t * 0.1)
            sd.lon_deg = 37.6184 + 0.0005 * math.cos(t * 0.1)
            sd.alt_m = 150 + 3 * math.sin(t * 0.2) + random.uniform(-1, 1)
            sd.speed_ms = 5 * abs(math.sin(t * 0.3)) + random.uniform(-0.5, 0.5)
            if sd.speed_ms < 0:
                sd.speed_ms = 0
            
            if self.data_callback:
                self.data_callback(sd)
            
            time.sleep(interval)
        
        if self.status_callback:
            self.status_callback(False)