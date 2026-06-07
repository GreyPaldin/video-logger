#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from gui.video_widget import VideoWidget
from gui.settings_window import SettingsWindow
from core.disk_monitor import DiskMonitor

class MainWindow(QMainWindow):
    def __init__(self, config_manager, video_capture, video_recorder, 
                 session_manager, mk_emulator, data_logger):
        super().__init__()
        self.config = config_manager
        self.video_capture = video_capture
        self.video_recorder = video_recorder
        self.session_manager = session_manager
        self.mk_emulator = mk_emulator
        self.data_logger = data_logger
        self.disk_monitor = DiskMonitor(config_manager)
        self.is_recording = False
        
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.update_video)
        self.disk_timer = QTimer()
        self.disk_timer.timeout.connect(self.update_disk_info)
        
        self.init_ui()
        self.init_connections()
        
        if self.mk_emulator is None:
            self.connection_status.setText("⭕ Эмулятор МК: отключён")
            self.connection_status.setStyleSheet("color: gray; font-weight: bold;")
        else:
            self.connection_status.setText("✅ Эмулятор МК: работает")
            self.connection_status.setStyleSheet("color: green; font-weight: bold;")
        
        self.open_camera()
        self.disk_timer.start(5000)
    
    def init_ui(self):
        self.setWindowTitle("Jetson Video & Data Logger")
        self.setGeometry(100, 100, 1280, 800)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)  # горизонтальный: видео слева, остальное справа
        
        # ========== ЛЕВАЯ ЧАСТЬ: ВИДЕО ==========
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.video_widget = VideoWidget()
        self.video_widget.setFixedSize(640, 480)  # увеличенный размер для наглядности
        self.video_widget.setScaledContents(True)
        left_layout.addWidget(self.video_widget, alignment=Qt.AlignCenter)
        left_layout.addStretch()
        main_layout.addWidget(left_widget, stretch=2)
        
        # ========== ПРАВАЯ ЧАСТЬ ==========
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # --- Верхняя панель с кнопками ---
        top_buttons = QHBoxLayout()
        self.settings_btn = QPushButton("⚙️ Настройки")
        self.start_btn = QPushButton("▶ Старт")
        self.stop_btn = QPushButton("⏹ Стоп")
        self.stop_btn.setEnabled(False)
        
        # Индикатор записи (красный кружок)
        self.record_indicator = QLabel()
        self.record_indicator.setFixedSize(20, 20)
        self.record_indicator.setStyleSheet("background-color: gray; border-radius: 10px;")
        
        for btn in [self.settings_btn, self.start_btn, self.stop_btn]:
            btn.setMinimumHeight(60)
            btn.setMinimumWidth(120)
            btn.setFont(QFont("Arial", 14, QFont.Bold))
        
        top_buttons.addWidget(self.record_indicator)
        top_buttons.addWidget(self.settings_btn)
        top_buttons.addWidget(self.start_btn)
        top_buttons.addWidget(self.stop_btn)
        top_buttons.addStretch()
        right_layout.addLayout(top_buttons)
        
        # --- Статус связи ---
        self.connection_status = QLabel()
        self.connection_status.setFont(QFont("Arial", 12))
        right_layout.addWidget(self.connection_status)
        
        # --- Панель датчиков ---
        sensors_group = QGroupBox("Текущие данные с датчиков")
        sensors_group.setFont(QFont("Arial", 14))
        sensors_layout = QGridLayout()
        self.encoder_label = QLabel("---")
        self.pitch_label = QLabel("---")
        self.roll_label = QLabel("---")
        self.gps_label = QLabel("---")
        for label in [self.encoder_label, self.pitch_label, self.roll_label, self.gps_label]:
            label.setFont(QFont("Arial", 14, QFont.Bold))
        
        sensors_layout.addWidget(QLabel("Энкодер:"), 0, 0)
        sensors_layout.addWidget(self.encoder_label, 0, 1)
        sensors_layout.addWidget(QLabel("Pitch:"), 1, 0)
        sensors_layout.addWidget(self.pitch_label, 1, 1)
        sensors_layout.addWidget(QLabel("Roll:"), 2, 0)
        sensors_layout.addWidget(self.roll_label, 2, 1)
        sensors_layout.addWidget(QLabel("GPS:"), 3, 0)
        sensors_layout.addWidget(self.gps_label, 3, 1, 1, 3)
        sensors_group.setLayout(sensors_layout)
        right_layout.addWidget(sensors_group)
        
        # --- Диск ---
        disk_group = QGroupBox("Диск")
        disk_layout = QVBoxLayout()
        self.disk_label = QLabel()
        self.disk_progress = QProgressBar()
        disk_layout.addWidget(self.disk_label)
        disk_layout.addWidget(self.disk_progress)
        disk_group.setLayout(disk_layout)
        right_layout.addWidget(disk_group)
        
        # --- Лог событий ---
        log_group = QGroupBox("События")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)
        
        main_layout.addWidget(right_widget, stretch=1)
        
        # Кнопочные действия
        self.settings_btn.clicked.connect(self.open_settings)
        self.start_btn.clicked.connect(self.start_recording)
        self.stop_btn.clicked.connect(self.stop_recording)
        
        self.statusBar().showMessage("Готов")
    
    def init_connections(self):
        self.session_manager.on_data_callback = self.update_sensor_display
        self.session_manager.on_rotation_callback = self.on_video_rotation
    
    def open_camera(self):
        if self.video_capture.open():
            self.video_timer.start(1000 // self.config.get('video', 'fps'))
            self.log_event("Камера открыта")
        else:
            self.log_event("⚠️ Камера не найдена! Превью недоступно")
    
    def update_video(self):
        frame = self.video_capture.read()
        if frame is not None:
            self.video_widget.update_frame(frame)
            if self.is_recording:
                rotated = self.video_recorder.write_frame(frame)
                if rotated:
                    self.log_event(f"Разбиение видео: часть {self.video_recorder.current_part_index - 1}")
    
    def update_sensor_display(self, sensor_data):
        self.encoder_label.setText(f"{sensor_data.encoder_deg:.1f}°")
        self.pitch_label.setText(f"{sensor_data.pitch_deg:.1f}°")
        self.roll_label.setText(f"{sensor_data.roll_deg:.1f}°")
        if sensor_data.gps_fix:
            self.gps_label.setText(f"fix: да | {sensor_data.lat_deg:.5f}, {sensor_data.lon_deg:.5f}")
        else:
            self.gps_label.setText("fix: нет | ожидание...")
    
    def update_disk_info(self):
        info = self.disk_monitor.get_disk_info()
        bitrate = self.config.get('video', 'bitrate_mbps')
        hours, minutes = self.disk_monitor.get_time_left(bitrate)
        self.disk_label.setText(
            f"Свободно: {info['free_gb']:.1f} ГБ / {info['total_gb']:.1f} ГБ  | "
            f"Хватит на: ~{hours}ч {minutes}м (при {bitrate} Мбит/с)"
        )
        self.disk_progress.setValue(int(info['used_percent']))
        if info['free_gb'] < 5:
            self.disk_label.setStyleSheet("color: red;")
            if self.is_recording:
                self.log_event("⚠️ КРИТИЧЕСКИ МАЛО МЕСТА!")
        else:
            self.disk_label.setStyleSheet("")
    
    def on_video_rotation(self, part_index):
        self.log_event(f"Новый видеофайл: часть {part_index}")
    
    def start_recording(self):
        if self.disk_monitor.is_critical(5):
            reply = QMessageBox.question(
                self, "Мало места",
                f"Осталось {self.disk_monitor.get_disk_info()['free_gb']:.1f} ГБ.\nПродолжить?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        self.is_recording = True
        self.session_manager.start_session()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.record_indicator.setStyleSheet("background-color: red; border-radius: 10px;")
        self.log_event("=== НАЧАЛО ЗАПИСИ ===")
        self.statusBar().showMessage("Запись идёт...")
    
    def stop_recording(self):
        self.is_recording = False
        self.session_manager.stop_session()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.record_indicator.setStyleSheet("background-color: gray; border-radius: 10px;")
        self.log_event("=== КОНЕЦ ЗАПИСИ ===")
        self.statusBar().showMessage("Запись остановлена")
    
    def open_settings(self):
        dialog = SettingsWindow(self.config, self)
        dialog.emulator_state_changed.connect(self.on_emulator_state_changed)
        cameras = self.video_capture.get_available_cameras()
        dialog.update_cameras(cameras)
        if dialog.exec_() == QDialog.Accepted:
            self.video_capture.apply_settings()
            self.video_recorder.apply_settings()
            self.video_timer.stop()
            self.video_capture.release()
            self.open_camera()
            if self.mk_emulator:
                self.mk_emulator.set_poll_hz(self.config.get('protocol', 'poll_hz'))
            self.log_event("Настройки применены")
    
    def on_emulator_state_changed(self, enabled):
        if enabled:
            if self.mk_emulator is None:
                from mk_interface.mk_emulator import MKEmulator
                self.mk_emulator = MKEmulator(self.config)
                def on_emulator_data(sensor_data):
                    self.session_manager.process_sensor_data(sensor_data)
                self.mk_emulator.data_callback = on_emulator_data
                self.mk_emulator.start()
                self.log_event("Эмулятор МК включён")
                self.connection_status.setText("✅ Эмулятор МК: работает")
                self.connection_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            if self.mk_emulator is not None:
                self.mk_emulator.stop()
                self.mk_emulator = None
                self.log_event("Эмулятор МК выключен")
                self.connection_status.setText("⭕ Эмулятор МК: отключён")
                self.connection_status.setStyleSheet("color: gray; font-weight: bold;")
    
    def log_event(self, message):
        timestamp = QTime.currentTime().toString("HH:mm:ss")
        self.log_text.append(f"[{timestamp}] {message}")
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        if self.is_recording:
            self.stop_recording()
        self.video_timer.stop()
        self.disk_timer.stop()
        self.video_capture.release()
        if self.mk_emulator:
            self.mk_emulator.stop()
        event.accept()