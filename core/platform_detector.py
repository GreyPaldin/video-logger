#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import platform

IS_WINDOWS = sys.platform == 'win32'
IS_LINUX = sys.platform == 'linux'
IS_JETSON = IS_LINUX and platform.machine() == 'aarch64'

def get_platform_name():
    if IS_JETSON:
        return "Jetson"
    elif IS_WINDOWS:
        return "Windows"
    else:
        return "Linux"

def is_emulation_needed():
    """Нужна ли эмуляция МК (на Windows, так как нет реального устройства)"""
    return IS_WINDOWS