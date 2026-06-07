#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from gui.video_widget import VideoWidget
from gui.settings_window import SettingsWindow
from core.disk_monitor import DiskMonitor

class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
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
        
        # Таймер для обновления видео
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.update_video)
        
        # Таймер для обновления диска
        self.disk_timer = QTimer()
        self.disk_timer.timeout.connect(self.update_disk_info)
        
        self.init_ui()
        self.init_connections()
        
        # Стартуем эмулятор МК
        self.mk_emulator.start()
        
        # Открываем камеру
        self.open_camera()
        
        # Таймеры
        self.disk_timer.start(5000)
    
    def init_ui(self):
        self.setWindowTitle("Jetson Video & Data Recorder (Эмуляция МК)")
        self.setGeometry(100, 100, 1280, 800)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Видео виджет
        self.video_widget = VideoWidget()
        layout.addWidget(self.video_widget)
        
        # Панель датчиков (заглушка)
        sensors_group = QGroupBox("Данные с датчиков (эмуляция)")
        sensors_layout = QGridLayout()
        
        self.encoder_label = QLabel("---")
        self.pitch_label = QLabel("---")
        self.roll_label = QLabel("---")
        self.gps_label = QLabel("---")
        
        sensors_layout.addWidget(QLabel("Энкодер (град):"), 0, 0)
        sensors_layout.addWidget(self.encoder_label, 0, 1)
        sensors_layout.addWidget(QLabel("Pitch (град):"), 1, 0)
        sensors_layout.addWidget(self.pitch_label, 1, 1)
        sensors_layout.addWidget(QLabel("Roll (град):"), 2, 0)
        sensors_layout.addWidget(self.roll_label, 2, 1)
        sensors_layout.addWidget(QLabel("GPS:"), 3, 0)
        sensors_layout.addWidget(self.gps_label, 3, 1, 1, 3)
        
        sensors_group.setLayout(sensors_layout)
        layout.addWidget(sensors_group)
        
        # Статус связи
        status_layout = QHBoxLayout()
        self.connection_status = QLabel("✅ Эмулятор МК: работает")
        self.connection_status.setStyleSheet("color: green; font-weight: bold;")
        status_layout.addWidget(self.connection_status)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # Диск
        disk_group = QGroupBox("Диск")
        disk_layout = QVBoxLayout()
        self.disk_label = QLabel()
        self.disk_progress = QProgressBar()
        disk_layout.addWidget(self.disk_label)
        disk_layout.addWidget(self.disk_progress)
        disk_group.setLayout(disk_layout)
        layout.addWidget(disk_group)
        
        # Лог событий
        log_group = QGroupBox("События")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        self.settings_btn = QPushButton("Настройки")
        self.start_btn = QPushButton("Старт")
        self.stop_btn = QPushButton("Стоп")
        self.stop_btn.setEnabled(False)
        
        self.settings_btn.clicked.connect(self.open_settings)
        self.start_btn.clicked.connect(self.start_recording)
        self.stop_btn.clicked.connect(self.stop_recording)
        
        btn_layout.addWidget(self.settings_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)
        
        self.statusBar().showMessage("Готов (эмуляция МК)")
    
    def init_connections(self):
        """Настройка колбэков"""
        self.session_manager.on_data_callback = self.update_sensor_display
        self.session_manager.on_rotation_callback = self.on_video_rotation
    
    def open_camera(self):
        """Открыть камеру и запустить таймер"""
        if self.video_capture.open():
            self.video_timer.start(1000 // self.config.get('video', 'fps'))
            self.log_event("Камера открыта")
        else:
            self.log_event("⚠️ Камера не найдена! Превью недоступно")
    
    def update_video(self):
        """Обновить видео (вызывается по таймеру)"""
        frame = self.video_capture.read()
        if frame is not None:
            self.video_widget.update_frame(frame)
            
            # Если идёт запись, передаём кадр в session_manager
            if self.is_recording:
                rotated = self.video_recorder.write_frame(frame)
                if rotated:
                    self.log_event(f"Разбиение видео: часть {self.video_recorder.current_part_index - 1}")
    
    def update_sensor_display(self, sensor_data):
        """Обновить отображение данных с датчиков"""
        self.encoder_label.setText(f"{sensor_data.encoder_deg:.1f}°")
        self.pitch_label.setText(f"{sensor_data.pitch_deg:.1f}°")
        self.roll_label.setText(f"{sensor_data.roll_deg:.1f}°")
        
        if sensor_data.gps_fix:
            self.gps_label.setText(f"fix: да | {sensor_data.lat_deg:.5f}, {sensor_data.lon_deg:.5f}")
        else:
            self.gps_label.setText("fix: нет | ожидание...")
    
    def update_disk_info(self):
        """Обновить информацию о диске"""
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
        """При разбиении видео"""
        self.log_event(f"Новый видеофайл: часть {part_index}")
    
    def start_recording(self):
        """Начать запись"""
        # Проверка места на диске
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
        self.log_event("=== НАЧАЛО ЗАПИСИ ===")
        self.statusBar().showMessage("Запись идёт...")
    
    def stop_recording(self):
        """Остановить запись"""
        self.is_recording = False
        self.session_manager.stop_session()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log_event("=== КОНЕЦ ЗАПИСИ ===")
        self.statusBar().showMessage("Запись остановлена")
    
    def open_settings(self):
        """Открыть окно настроек"""
        dialog = SettingsWindow(self.config, self)
        
        # Обновляем список камер
        cameras = self.video_capture.get_available_cameras()
        dialog.update_cameras(cameras)
        
        if dialog.exec_() == QDialog.Accepted:
            # Применяем настройки
            self.video_capture.apply_settings()
            self.video_recorder.apply_settings()
            
            # Перезапускаем камеру с новыми настройками
            self.video_timer.stop()
            self.video_capture.release()
            self.open_camera()
            
            # Обновляем эмулятор
            self.mk_emulator.set_poll_hz(self.config.get('protocol', 'poll_hz'))
            
            self.log_event("Настройки применены")
    
    def log_event(self, message):
        """Добавить событие в лог"""
        timestamp = QTime.currentTime().toString("HH:mm:ss")
        self.log_text.append(f"[{timestamp}] {message}")
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """При закрытии окна"""
        if self.is_recording:
            self.stop_recording()
        self.video_timer.stop()
        self.disk_timer.stop()
        self.video_capture.release()
        self.mk_emulator.stop()
        event.accept()