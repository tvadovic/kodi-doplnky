# -*- coding: utf-8 -*-
"""Perzistentné dáta doplnku: cache, Pozrieť neskôr a história hľadania.

Všetko sú JSON súbory v adresári profilu doplnku
(special://profile/addon_data/plugin.video.stvr/). Modul nepoužíva xbmc*,
adresár dostane zvonku.
"""

import hashlib
import json
import os
import shutil
import tempfile
import time


def _read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (IOError, OSError, ValueError):
        return default


def _write_json(path, data):
    """Atomický zápis: dočasný súbor + os.replace, aby pád nezničil dáta."""
    folder = os.path.dirname(path)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    fd, tmp = tempfile.mkstemp(dir=folder, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


class Cache(object):
    """Jednoduchá súborová cache s TTL. Kľúč je ľubovoľný reťazec (typicky URL)."""

    def __init__(self, folder):
        self.folder = folder

    def _path(self, key):
        return os.path.join(self.folder, hashlib.sha1(key.encode("utf-8")).hexdigest() + ".json")

    def get(self, key, ttl):
        entry = _read_json(self._path(key), None)
        if not isinstance(entry, dict) or entry.get("key") != key:
            return None
        if time.time() - entry.get("ts", 0) > ttl:
            return None
        return entry.get("value")

    def set(self, key, value):
        try:
            _write_json(self._path(key), {"key": key, "ts": time.time(), "value": value})
        except (IOError, OSError):
            pass  # cache nie je kritická

    def clear(self):
        shutil.rmtree(self.folder, ignore_errors=True)


class WatchLater(object):
    """Zoznam „Pozrieť neskôr“: relácie (kind="show") aj epizódy (kind="episode").

    Položka obsahuje všetko potrebné na zobrazenie bez siete:
    {"kind", "id", "title", "image", "plot", "show_id", "show_title", "date", "added"}.
    Stream URL sa sem nikdy neukladá, iba ID epizódy.
    """

    FIELDS = ("title", "image", "plot", "show_id", "show_title", "date")

    def __init__(self, path):
        self.path = path

    def items(self):
        data = _read_json(self.path, [])
        return data if isinstance(data, list) else []

    def contains(self, kind, item_id):
        return any(i.get("kind") == kind and i.get("id") == str(item_id) for i in self.items())

    def add(self, kind, item_id, **info):
        items = [i for i in self.items()
                 if not (i.get("kind") == kind and i.get("id") == str(item_id))]
        entry = {"kind": kind, "id": str(item_id), "added": int(time.time())}
        entry.update((k, info.get(k) or "") for k in self.FIELDS)
        items.insert(0, entry)
        _write_json(self.path, items)

    def remove(self, kind, item_id):
        items = self.items()
        kept = [i for i in items if not (i.get("kind") == kind and i.get("id") == str(item_id))]
        if len(kept) != len(items):
            _write_json(self.path, kept)
            return True
        return False


class SearchHistory(object):
    """Posledné hľadané výrazy (najnovší prvý, bez duplicít)."""

    def __init__(self, path, limit=20):
        self.path = path
        self.limit = limit

    def items(self):
        data = _read_json(self.path, [])
        return [q for q in data if isinstance(q, str)] if isinstance(data, list) else []

    def add(self, query):
        query = query.strip()
        if not query:
            return
        items = [q for q in self.items() if q.lower() != query.lower()]
        _write_json(self.path, ([query] + items)[:self.limit])

    def remove(self, query):
        _write_json(self.path, [q for q in self.items() if q != query])

    def clear(self):
        _write_json(self.path, [])
