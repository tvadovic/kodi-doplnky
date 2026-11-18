# -*- coding: utf-8 -*-
"""Stub xbmcvfs: special:// cesty smerujú do dev/profile (alebo STVR_PROFILE)."""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _base():
    return os.environ.get("STVR_PROFILE") or os.path.join(ROOT, "dev", "profile")


def translatePath(path):
    for prefix, target in (("special://profile/", "userdata"), ("special://temp/", "temp"),
                           ("special://home/", "home")):
        if path.startswith(prefix):
            return os.path.join(_base(), target, *path[len(prefix):].split("/"))
    return path


def exists(path):
    return os.path.exists(path)


def mkdirs(path):
    os.makedirs(path, exist_ok=True)
    return True
