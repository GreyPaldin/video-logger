#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class SettingsWindow(QDialog):
    emulator_state_changed = pyqtSignal(bool)
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.init_ui()
        self.load_from_config()
    
    def init_ui(self):
        self.setWindowTitle("Настройки")
        self.setModal(True)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        # Общий шрифт для всех виджетов
        font = QFont("Arial", 12)
        self.setFont(font)
        
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.setFont(font)
        
        # --- Вкладка ВИДЕО ---
        video_tab = QWidget()
        video_layout = QFormLayout(video_tab)
        video_layout.setSpacing(15)
        self.camera_combo = QComboBox()
        self.camera_combo.setFont(font)
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1920x1080", "1280x720", "640x480"])
        self.resolution_combo.setFont(font)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setSuffix(" fps")
        self.fps_spin.setFont(font)
        self.bitrate_spin = QSpinBox()
        self.bitrate_spin.setRange(1, 50)
        self.bitrate_spin.setSuffix(" Мбит/с")
        self.bitrate_spin.setFont(font)
        self.video_folder_edit = QLineEdit()
        self.video_folder_edit.setFont(font)
        self.video_folder_btn = QPushButton("Обзор...")
        self.video_folder_btn.setFont(font)
        self.video_folder_btn.setMinimumHeight(40)
        self.video_folder_btn.clicked.connect(lambda: self._browse_folder(self.video_folder_edit))
        video_folder_layout = QHBoxLayout()
        video_folder_layout.addWidget(self.video_folder_edit)
        video_folder_layout.addWidget(self.video_folder_btn)
        self.segment_spin = QSpinBox()
        self.segment_spin.setRange(10, 3600)
        self.segment_spin.setSuffix(" сек")
        self.segment_spin.setFont(font)
        
        video_layout.addRow("Камера:", self.camera_combo)
        video_layout.addRow("Разрешение:", self.resolution_combo)
        video_layout.addRow("FPS:", self.fps_spin)
        video_layout.addRow("Битрейт:", self.bitrate_spin)
        video_layout.addRow("Папка видео:", video_folder_layout)
        video_layout.addRow("Длительность файла:", self.segment_spin)
        
        # --- Вкладка ПРОТОКОЛ ---
        proto_tab = QWidget()
        proto_layout = QFormLayout(proto_tab)
        proto_layout.setSpacing(15)
        self.poll_hz_spin = QDoubleSpinBox()
        self.poll_hz_spin.setRange(1, 100)
        self.poll_hz_spin.setSuffix(" Гц")
        self.poll_hz_spin.setFont(font)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 1000)
        self.timeout_spin.setSuffix(" мс")
        self.timeout_spin.setFont(font)
        self.retries_spin = QSpinBox()
        self.retries_spin.setRange(1, 10)
        self.retries_spin.setSuffix(" раз")
        self.retries_spin.setFont(font)
        proto_layout.addRow("Частота опроса:", self.poll_hz_spin)
        proto_layout.addRow("Таймаут ответа:", self.timeout_spin)
        proto_layout.addRow("Количество попыток:", self.retries_spin)
        
        # --- Вкладка ЛОГИРОВАНИЕ ---
        log_tab = QWidget()
        log_layout = QFormLayout(log_tab)
        log_layout.setSpacing(15)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["csv", "json", "both"])
        self.format_combo.setFont(font)
        self.log_folder_edit = QLineEdit()
        self.log_folder_edit.setFont(font)
        self.log_folder_btn = QPushButton("Обзор...")
        self.log_folder_btn.setFont(font)
        self.log_folder_btn.setMinimumHeight(40)
        self.log_folder_btn.clicked.connect(lambda: self._browse_folder(self.log_folder_edit))
        log_folder_layout = QHBoxLayout()
        log_folder_layout.addWidget(self.log_folder_edit)
        log_folder_layout.addWidget(self.log_folder_btn)
        log_layout.addRow("Формат сохранения:", self.format_combo)
        log_layout.addRow("Папка логов:", log_folder_layout)
        
        # --- Вкладка СИСТЕМА ---
        system_tab = QWidget()
        system_layout = QFormLayout(system_tab)
        system_layout.setSpacing(15)
        self.emulator_checkbox = QCheckBox("Использовать эмулятор МК")
        self.emulator_checkbox.setFont(QFont("Arial", 14))
        system_layout.addRow("", self.emulator_checkbox)
        
        tabs.addTab(video_tab, "Видео")
        tabs.addTab(proto_tab, "Протокол")
        tabs.addTab(log_tab, "Логирование")
        tabs.addTab(system_tab, "Система")
        layout.addWidget(tabs)
        
        # Кнопки внизу
        buttons = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отменить")
        self.reset_btn = QPushButton("Сбросить к стандартным")
        self.close_btn = QPushButton("Закрыть")
        
        for btn in [self.save_btn, self.cancel_btn, self.reset_btn, self.close_btn]:
            btn.setMinimumHeight(50)
            btn.setMinimumWidth(120)
            btn.setFont(QFont("Arial", 12, QFont.Bold))
        
        self.save_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self.cancel_btn.setStyleSheet("background-color: #f44336; color: white;")
        
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)
        buttons.addWidget(self.reset_btn)
        buttons.addWidget(self.close_btn)
        layout.addLayout(buttons)
        
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn.clicked.connect(self.cancel_settings)
        self.reset_btn.clicked.connect(self.reset_settings)
        self.close_btn.clicked.connect(self.accept)
    
    def _browse_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder:
            line_edit.setText(folder)
    
    def load_from_config(self):
        res = f"{self.config.get('video', 'width')}x{self.config.get('video', 'height')}"
        idx = self.resolution_combo.findText(res)
        if idx >= 0:
            self.resolution_combo.setCurrentIndex(idx)
        self.fps_spin.setValue(self.config.get('video', 'fps'))
        self.bitrate_spin.setValue(self.config.get('video', 'bitrate_mbps'))
        self.video_folder_edit.setText(self.config.get('video', 'video_folder'))
        self.segment_spin.setValue(self.config.get('video', 'segment_duration_sec'))
        self.poll_hz_spin.setValue(self.config.get('protocol', 'poll_hz'))
        self.timeout_spin.setValue(self.config.get('protocol', 'timeout_ms'))
        self.retries_spin.setValue(self.config.get('protocol', 'retries'))
        fmt = self.config.get('logging', 'format')
        idx = self.format_combo.findText(fmt)
        if idx >= 0:
            self.format_combo.setCurrentIndex(idx)
        self.log_folder_edit.setText(self.config.get('logging', 'log_folder'))
        
        emul_on = self.config.get('system', 'emulator_enabled')
        if emul_on is None:
            emul_on = True
        self.emulator_checkbox.setChecked(emul_on)
    
    def save_settings(self):
        res = self.resolution_combo.currentText().split('x')
        self.config.set(int(res[0]), 'video', 'width')
        self.config.set(int(res[1]), 'video', 'height')
        self.config.set(self.fps_spin.value(), 'video', 'fps')
        self.config.set(self.bitrate_spin.value(), 'video', 'bitrate_mbps')
        self.config.set(self.video_folder_edit.text(), 'video', 'video_folder')
        self.config.set(self.segment_spin.value(), 'video', 'segment_duration_sec')
        self.config.set(int(self.poll_hz_spin.value()), 'protocol', 'poll_hz')
        self.config.set(self.timeout_spin.value(), 'protocol', 'timeout_ms')
        self.config.set(self.retries_spin.value(), 'protocol', 'retries')
        self.config.set(self.format_combo.currentText(), 'logging', 'format')
        self.config.set(self.log_folder_edit.text(), 'logging', 'log_folder')
        
        new_state = self.emulator_checkbox.isChecked()
        self.config.set(new_state, 'system', 'emulator_enabled')
        self.config.save()
        
        self.emulator_state_changed.emit(new_state)
        QMessageBox.information(self, "Успех", "Настройки сохранены")
        self.accept()
    
    def cancel_settings(self):
        self.load_from_config()
        QMessageBox.information(self, "Отмена", "Изменения отменены")
    
    def reset_settings(self):
        reply = QMessageBox.question(self, "Сброс", "Сбросить все настройки?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.config.reset_to_default()
            self.load_from_config()
            QMessageBox.information(self, "Сброс", "Настройки сброшены")
    
    def update_cameras(self, cameras):
        self.camera_combo.clear()
        self.camera_combo.addItems(cameras)
        current = self.config.get('video', 'camera_id')
        if current and current in cameras:
            self.camera_combo.setCurrentText(current)
        elif cameras:
            self.camera_combo.setCurrentIndex(0)
            self.config.set(cameras[0], 'video', 'camera_id')