#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
from pathlib import Path

class DiskMonitor:
    """Мониторинг свободного места на диске и прогноз времени записи"""
    
    def __init__(self, config_manager):
        self.config = config_manager
    
    def get_disk_info(self):
        """Вернуть информацию о диске: свободно ГБ, всего ГБ, процент использования"""
        log_folder = Path(self.config.get('logging', 'log_folder'))
        log_folder.mkdir(parents=True, exist_ok=True)
        
        stat = shutil.disk_usage(log_folder)
        free_gb = stat.free / (1024**3)
        total_gb = stat.total / (1024**3)
        used_percent = (stat.used / stat.total) * 100
        
        return {
            'free_gb': free_gb,
            'total_gb': total_gb,
            'used_percent': used_percent
        }
    
    def get_time_left(self, bitrate_mbps=None):
        """
        Прогноз времени записи в часах при текущем битрейте
        Возвращает (часы, минуты)
        """
        if bitrate_mbps is None:
            bitrate_mbps = self.config.get('video', 'bitrate_mbps')
        
        info = self.get_disk_info()
        free_gb = info['free_gb']
        
        # Примерная формула: Мбит/с * 0.45 = ГБ/час
        gb_per_hour = bitrate_mbps * 0.45
        
        if gb_per_hour <= 0:
            return (0, 0)
        
        hours_left = free_gb / gb_per_hour
        hours = int(hours_left)
        minutes = int((hours_left - hours) * 60)
        
        return (hours, minutes)
    
    def is_critical(self, threshold_gb=5):
        """Проверить, не критически ли мало места"""
        info = self.get_disk_info()
        return info['free_gb'] < threshold_gb