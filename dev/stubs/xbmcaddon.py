# -*- coding: utf-8 -*-
"""Stub xbmcaddon: číta addon.xml, predvolené nastavenia a strings.po z repozitára."""
import os
import re
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "plugin.video.stvr"))
SETTINGS = {}   # prepísané nastavenia (dev/run.py --set, testy)


def _strings():
    lang = "resource.language.en_gb" if os.environ.get("KODI_LANG") == "en" else "resource.language.sk_sk"
    with open(os.path.join(ROOT, "resources", "language", lang, "strings.po"), encoding="utf-8") as f:
        text = f.read()
    result = {}
    for ctx, msgid, msgstr in re.findall(r'msgctxt "#(\d+)"\nmsgid "(.*)"\nmsgstr "(.*)"', text):
        result[int(ctx)] = (msgstr or msgid).replace('\\"', '"')
    return result


def _defaults():
    tree = ET.parse(os.path.join(ROOT, "resources", "settings.xml"))
    return dict((s.get("id"), (s.get("type"), s.findtext("default")))
                for s in tree.iter("setting"))


class Addon(object):
    def __init__(self, addon_id=None):
        tree = ET.parse(os.path.join(ROOT, "addon.xml")).getroot()
        self._info = {
            "id": tree.get("id"), "name": tree.get("name"), "version": tree.get("version"),
            "path": ROOT, "icon": os.path.join(ROOT, "icon.png"), "fanart": os.path.join(ROOT, "fanart.jpg"),
            "profile": "special://profile/addon_data/%s/" % tree.get("id"),
        }
        self._strings = _strings()
        self._defaults = _defaults()

    def getAddonInfo(self, key):
        return self._info.get(key, "")

    def getLocalizedString(self, string_id):
        return self._strings.get(string_id, "")

    def _raw(self, key):
        if key in SETTINGS:
            return str(SETTINGS[key])
        return (self._defaults.get(key) or (None, ""))[1] or ""

    def getSetting(self, key):
        return self._raw(key)

    def getSettingBool(self, key):
        return self._raw(key).lower() == "true"

    def getSettingInt(self, key):
        return int(self._raw(key) or 0)

    def setSetting(self, key, value):
        SETTINGS[key] = value
