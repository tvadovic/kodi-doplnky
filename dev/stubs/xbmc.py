# -*- coding: utf-8 -*-
"""Stub modulu xbmc pre spúšťanie doplnku mimo Kodi (dev/run.py, testy)."""
import os
import sys

LOGDEBUG, LOGINFO, LOGWARNING, LOGERROR, LOGFATAL = 0, 1, 2, 3, 4
BUILTINS = []          # zaznamenané executebuiltin príkazy
KEYBOARD_INPUT = []    # odpovede pre Keyboard (FIFO); prázdne = zrušené
INSTALLED_ADDONS = set()


def log(msg, level=LOGDEBUG):
    if level >= LOGWARNING or os.environ.get("STVR_DEBUG"):
        sys.stderr.write("[log %d] %s\n" % (level, msg))


def executebuiltin(command, wait=False):
    BUILTINS.append(command)
    sys.stderr.write("[builtin] %s\n" % command)


def getCondVisibility(condition):
    if condition.startswith("System.HasAddon("):
        return condition[16:-1] in INSTALLED_ADDONS
    return False


def getInfoLabel(label):
    return "21.2.0 (21.2.0) Git:stub" if label == "System.BuildVersion" else ""


class Keyboard(object):
    def __init__(self, default="", heading="", hidden=False):
        self._text, self._ok = default, False

    def doModal(self):
        if KEYBOARD_INPUT:
            self._text, self._ok = KEYBOARD_INPUT.pop(0), True

    def isConfirmed(self):
        return self._ok

    def getText(self):
        return self._text


class VideoStreamDetail(object):
    def __init__(self, width=0, height=0, aspect=0.0, duration=0, codec="", stereomode="", language="", hdrtype=""):
        self.width, self.height, self.codec = width, height, codec
