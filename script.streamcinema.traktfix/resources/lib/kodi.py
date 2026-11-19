# -*- coding: utf-8 -*-
import os

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from resources.lib import patcher

ADDON = xbmcaddon.Addon()
NAME = ADDON.getAddonInfo('name')
ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')

SC_TRAKT_DIR = xbmcvfs.translatePath(
    'special://home/addons/plugin.video.stream-cinema/resources/lib/trakt')
PATCH_DIR = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'patch')

# action=trakt.list (Stream Cinema koduje hodnoty v URL do hex)
TRAKT_FOLDER = 'plugin://plugin.video.stream-cinema/?action=7472616b742e6c697374'


def log(msg):
    xbmc.log('[{}] {}'.format(ADDON.getAddonInfo('id'), msg), xbmc.LOGINFO)


def notify(msg, ms=8000):
    xbmcgui.Dialog().notification(NAME, msg, ICON, ms)


def ensure_patch():
    try:
        state = patcher.apply(SC_TRAKT_DIR, PATCH_DIR)
    except Exception as e:  # zapis do suborov doplnku zlyhal
        log('chyba: {!r}'.format(e))
        notify('Opravu sa nepodarilo nahrať: {}'.format(e))
        return patcher.UNKNOWN
    log('stav opravy: {}'.format(state))
    return state
