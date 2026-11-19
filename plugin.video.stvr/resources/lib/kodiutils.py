# -*- coding: utf-8 -*-
"""Tenká vrstva nad Kodi API: nastavenia, preklady, notifikácie, cesty."""

import os

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")
ADDON_NAME = ADDON.getAddonInfo("name")
ADDON_VERSION = ADDON.getAddonInfo("version")
ADDON_ICON = ADDON.getAddonInfo("icon")
ADDON_FANART = ADDON.getAddonInfo("fanart")
PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))


def profile_path(*parts):
    return os.path.join(PROFILE, *parts)


def tr(string_id):
    return ADDON.getLocalizedString(string_id)


def setting_bool(key, default=False):
    try:
        return ADDON.getSettingBool(key)
    except (RuntimeError, TypeError):
        return default


def setting_int(key, default=0):
    try:
        return ADDON.getSettingInt(key)
    except (RuntimeError, TypeError):
        return default


def log(message, level=xbmc.LOGDEBUG):
    xbmc.log("[%s] %s" % (ADDON_ID, message), level)


def notify(message, error=False):
    icon = xbmcgui.NOTIFICATION_ERROR if error else ADDON_ICON
    xbmcgui.Dialog().notification(ADDON_NAME, message, icon, 5000)


def ok_dialog(message):
    xbmcgui.Dialog().ok(ADDON_NAME, message)


def keyboard(heading, default=""):
    kb = xbmc.Keyboard(default, heading)
    kb.doModal()
    return kb.getText().strip() if kb.isConfirmed() else None


def has_addon(addon_id):
    return bool(xbmc.getCondVisibility("System.HasAddon(%s)" % addon_id))


def builtin(command):
    xbmc.executebuiltin(command)
