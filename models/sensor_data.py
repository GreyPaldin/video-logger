#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class SensorData:
    """Структура данных с датчиков (масштабированные значения)"""
    
    def __init__(self):
        self.time_abs = 0.0      # абсолютное время от старта сессии (сек)
        self.time_file = 0.0     # время от начала текущего файла (сек)
        
        # Данные с энкодера и IMU
        self.encoder_deg = 0.0
        self.pitch_deg = 0.0
        self.roll_deg = 0.0
        self.ax_ms2 = 0.0
        self.ay_ms2 = 0.0
        self.az_ms2 = 0.0
        self.gx_dps = 0.0
        self.gy_dps = 0.0
        self.gz_dps = 0.0
        
        # GPS данные
        self.gps_fix = 0
        self.lat_deg = 0.0
        self.lon_deg = 0.0
        self.alt_m = 0.0
        self.speed_ms = 0.0
    
    def to_dict(self):
        return {
            'time_abs_sec': round(self.time_abs, 3),
            'time_file_sec': round(self.time_file, 3),
            'encoder_deg': round(self.encoder_deg, 2),
            'pitch_deg': round(self.pitch_deg, 2),
            'roll_deg': round(self.roll_deg, 2),
            'Ax_ms2': round(self.ax_ms2, 3),
            'Ay_ms2': round(self.ay_ms2, 3),
            'Az_ms2': round(self.az_ms2, 3),
            'Gx_dps': round(self.gx_dps, 2),
            'Gy_dps': round(self.gy_dps, 2),
            'Gz_dps': round(self.gz_dps, 2),
            'gps_fix': self.gps_fix,
            'lat_deg': round(self.lat_deg, 7),
            'lon_deg': round(self.lon_deg, 7),
            'alt_m': round(self.alt_m, 1),
            'speed_ms': round(self.speed_ms, 2)
        }
    
    def to_csv_line(self):
        """Преобразовать в строку CSV (с заголовком)"""
        d = self.to_dict()
        return f"{d['time_abs_sec']},{d['time_file_sec']},{d['encoder_deg']},{d['pitch_deg']},{d['roll_deg']},{d['Ax_ms2']},{d['Ay_ms2']},{d['Az_ms2']},{d['Gx_dps']},{d['Gy_dps']},{d['Gz_dps']},{d['gps_fix']},{d['lat_deg']},{d['lon_deg']},{d['alt_m']},{d['speed_ms']}\n"


# CSV заголовок (шапка)
CSV_HEADER = "time_abs_sec,time_file_sec,encoder_deg,pitch_deg,roll_deg,Ax_ms2,Ay_ms2,Az_ms2,Gx_dps,Gy_dps,Gz_dps,gps_fix,lat_deg,lon_deg,alt_m,speed_ms\n"