# -*- coding: utf-8 -*-
"""Stub xbmcplugin: zaznamená položky adresára a výsledok setResolvedUrl."""

ITEMS = []        # (url, ListItem, isFolder)
STATE = {}        # content, succeeded, resolved…


def reset():
    del ITEMS[:]
    STATE.clear()


def addDirectoryItem(handle, url, listitem, isFolder=False, totalItems=0):
    ITEMS.append((url, listitem, isFolder))
    return True


def addDirectoryItems(handle, items, totalItems=0):
    for url, li, folder in items:
        addDirectoryItem(handle, url, li, folder)
    return True


def setContent(handle, content):
    STATE["content"] = content


def endOfDirectory(handle, succeeded=True, updateListing=False, cacheToDisc=True):
    STATE["succeeded"] = succeeded


def setResolvedUrl(handle, succeeded, listitem):
    STATE["resolved"] = (succeeded, listitem)
