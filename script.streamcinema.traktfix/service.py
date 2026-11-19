# -*- coding: utf-8 -*-
from resources.lib import patcher
from resources.lib.kodi import ensure_patch, notify

state = ensure_patch()
if state == patcher.APPLIED:
    notify('Oprava Trakt nahraná. Ak už Stream Cinema bežalo, reštartuj Kodi.')
elif state == patcher.UNKNOWN:
    notify('Stream Cinema má inú verziu súborov, oprava Trakt sa nenahrala.')
