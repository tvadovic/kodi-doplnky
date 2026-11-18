# -*- coding: utf-8 -*-
"""Stub xbmcgui: ListItem, InfoTagVideo a Dialog (zapisuje do zoznamov namiesto UI)."""
import sys

NOTIFICATION_INFO, NOTIFICATION_WARNING, NOTIFICATION_ERROR = "info", "warning", "error"
NOTIFICATIONS = []
DIALOGS = []


class InfoTagVideo(object):
    def __init__(self):
        self.info = {}

    def __getattr__(self, name):
        if name.startswith("set") or name.startswith("add"):
            def setter(value, *args):
                if name.startswith("add"):
                    self.info.setdefault(name[3:].lower(), []).append(value)
                else:
                    self.info[name[3:].lower()] = value
            return setter
        raise AttributeError(name)


class ListItem(object):
    def __init__(self, label="", label2="", path="", offscreen=False):
        self.label, self.path = label, path
        self.art, self.properties, self.context = {}, {}, []
        self.subtitles, self.mimetype, self.tag = [], "", InfoTagVideo()

    def getLabel(self):
        return self.label

    def getPath(self):
        return self.path

    def setPath(self, path):
        self.path = path

    def setArt(self, art):
        self.art.update(art)

    def setProperty(self, key, value):
        self.properties[key] = value

    def getProperty(self, key):
        return self.properties.get(key, "")

    def getVideoInfoTag(self):
        return self.tag

    def addContextMenuItems(self, items, replaceItems=False):
        self.context.extend(items)

    def setSubtitles(self, subtitles):
        self.subtitles = list(subtitles)

    def setMimeType(self, mimetype):
        self.mimetype = mimetype

    def setContentLookup(self, enable):
        pass


class Dialog(object):
    def notification(self, heading, message, icon=NOTIFICATION_INFO, time=5000, sound=True):
        NOTIFICATIONS.append(message)
        sys.stderr.write("[notification] %s\n" % message)

    def ok(self, heading, message):
        DIALOGS.append(message)
        sys.stderr.write("[dialog] %s\n" % message)
        return True
