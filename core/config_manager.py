#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "video": {
        "camera_id": "",
        "width": 1280,
        "height": 720,
        "fps": 30,
        "bitrate_mbps": 5,
        "video_folder": str(Path.home() / "video_recorder" / "videos"),
        "segment_duration_sec": 300
    },
    "protocol": {
        "poll_hz": 30,
        "timeout_ms": 100,
        "retries": 3,
        "ping_interval_sec": 2
    },
    "logging": {
        "format": "csv",
        "log_folder": str(Path.home() / "video_recorder" / "logs")
    },
    "system": {
        "emulator_enabled": True
    }
}

class ConfigManager:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = DEFAULT_CONFIG.copy()
        self.load()
    
    def load(self):
        """Загрузить настройки из файла"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded = json.load(f)
                    self._update_recursive(self.config, loaded)
            except Exception as e:
                print(f"Ошибка загрузки конфига: {e}")
    
    def save(self):
        """Сохранить настройки в файл"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения конфига: {e}")
    
    def get(self, *keys):
        """Получить значение по ключам: get('video', 'width')"""
        value = self.config
        for key in keys:
            value = value.get(key)
            if value is None:
                return None
        return value
    
    def set(self, value, *keys):
        """Установить значение по ключам"""
        target = self.config
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value
    
    def _update_recursive(self, target, source):
        """Рекурсивное обновление словаря"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_recursive(target[key], value)
            else:
                target[key] = value
    
    def reset_to_default(self):
        """Сбросить настройки к стандартным"""
        self.config = DEFAULT_CONFIG.copy()