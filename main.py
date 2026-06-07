#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication

from core.config_manager import ConfigManager
from core.video_capture import VideoCapture
from core.video_recorder import VideoRecorder
from core.data_logger import DataLogger
from core.session_manager import SessionManager
from mk_interface.mk_emulator import MKEmulator
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    config = ConfigManager()
    
    video_capture = VideoCapture(config)
    video_recorder = VideoRecorder(config)
    data_logger = DataLogger(config)
    session_manager = SessionManager(video_recorder, data_logger)
    
    emulator_enabled = config.get('system', 'emulator_enabled')
    if emulator_enabled:
        mk_emulator = MKEmulator(config)
        def on_emulator_data(sensor_data):
            session_manager.process_sensor_data(sensor_data)
        mk_emulator.data_callback = on_emulator_data
        mk_emulator.start()
        print("Эмулятор МК запущен")
    else:
        mk_emulator = None
        print("Эмулятор МК отключён")
    
    window = MainWindow(config, video_capture, video_recorder, session_manager, mk_emulator, data_logger)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()