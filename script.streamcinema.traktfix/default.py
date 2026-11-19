# -*- coding: utf-8 -*-
import xbmc
import xbmcgui

from resources.lib import patcher
from resources.lib.kodi import NAME, TRAKT_FOLDER, ensure_patch

state = ensure_patch()
if state == patcher.MISSING:
    xbmcgui.Dialog().ok(NAME, 'Doplnok Stream Cinema CZ a SK nie je nainštalovaný.')
elif state == patcher.APPLIED:
    xbmcgui.Dialog().ok(NAME, 'Oprava Trakt bola práve nahraná.[CR]'
                              'Reštartuj Kodi, potom to spusti znova.')
else:
    if state == patcher.UNKNOWN:
        xbmcgui.Dialog().notification(
            NAME, 'Stream Cinema má inú verziu, oprava sa nenahrala.',
            xbmcgui.NOTIFICATION_WARNING, 6000)
    # bez ",return": inak Kodi pri navrate otvori koren doplnku namiesto priecinka
    xbmc.executebuiltin('ActivateWindow(Videos,"{}")'.format(TRAKT_FOLDER))
