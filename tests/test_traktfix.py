# -*- coding: utf-8 -*-
"""Testy doplnku script.streamcinema.traktfix (oprava Trakt pre Stream Cinema)."""
import ast
import hashlib
import importlib.util
import os
import shutil
import xml.etree.ElementTree as ET
import zipfile

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ADDON_DIR = os.path.join(ROOT, "script.streamcinema.traktfix")
PATCH_DIR = os.path.join(ADDON_DIR, "resources", "patch")


def _load(path, name):
    # resources/ tohto doplnku by kolidoval s resources/ plugin.video.stvr na sys.path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


patcher = _load(os.path.join(ADDON_DIR, "resources", "lib", "patcher.py"), "traktfix_patcher")
build_zip = _load(os.path.join(ROOT, "dev", "build_zip.py"), "build_zip")


def _sha(data):
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def sc(tmp_path):
    """Falošný priečinok trakt/ v Stream Cinema s „pôvodnými“ súbormi a ich odtlačkami."""
    target = tmp_path / "trakt"
    target.mkdir()
    originals = {}
    for name in patcher.ORIGINALS:
        data = ("# povodny %s\r\n" % name).encode()
        (target / name).write_bytes(data)
        originals[name] = {_sha(data)}
    return str(target), originals


def _read(folder, name):
    with open(os.path.join(folder, name), "rb") as f:
        return f.read()


def test_apply_then_already_patched(sc):
    target, originals = sc
    before = {n: _read(target, n) for n in originals}
    assert patcher.apply(target, PATCH_DIR, originals) == patcher.APPLIED
    for name in originals:
        assert _read(target, name) == _read(PATCH_DIR, name)
        assert _read(target, name + ".orig") == before[name]
    assert not [n for n in os.listdir(target) if n.endswith(".new")]
    assert patcher.apply(target, PATCH_DIR, originals) == patcher.PATCHED


def test_unknown_version_changes_nothing(sc):
    target, originals = sc
    with open(os.path.join(target, "api.py"), "ab") as f:
        f.write(b"# nova verzia Stream Cinema\r\n")
    before = {n: _read(target, n) for n in os.listdir(target)}
    assert patcher.apply(target, PATCH_DIR, originals) == patcher.UNKNOWN
    # ani Trakt.py (známy) sa neprepíše, oprava je vždy celá alebo žiadna
    assert {n: _read(target, n) for n in os.listdir(target)} == before


def test_partially_patched_finishes(sc):
    target, originals = sc
    shutil.copyfile(os.path.join(PATCH_DIR, "Trakt.py"), os.path.join(target, "Trakt.py"))
    assert patcher.apply(target, PATCH_DIR, originals) == patcher.APPLIED
    assert _read(target, "api.py") == _read(PATCH_DIR, "api.py")
    assert not os.path.exists(os.path.join(target, "Trakt.py.orig"))


def test_missing_stream_cinema(tmp_path):
    assert patcher.apply(str(tmp_path / "nie"), PATCH_DIR) == patcher.MISSING


def test_missing_file_is_unknown(sc):
    target, originals = sc
    os.remove(os.path.join(target, "api.py"))
    assert patcher.apply(target, PATCH_DIR, originals) == patcher.UNKNOWN


@pytest.mark.parametrize("name", sorted(patcher.ORIGINALS))
def test_patch_files_kept_byte_exact(name):
    # Stream Cinema má konce riadkov LF; CR by znamenalo, že ich git/editor zmenil
    data = _read(PATCH_DIR, name)
    assert b"\r" not in data and data.count(b"\n") > 0
    assert _sha(data) not in patcher.ORIGINALS[name]  # opravený ≠ pôvodný
    ast.parse(data.decode("utf-8"), feature_version=(3, 8))  # Kodi 21 = Python 3.8


def test_addon_sources_parse_for_python38():
    for folder, dirs, files in os.walk(ADDON_DIR):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            if name.endswith(".py"):
                with open(os.path.join(folder, name), encoding="utf-8") as f:
                    ast.parse(f.read(), feature_version=(3, 8))


def test_addon_xml_and_zip(tmp_path):
    root = ET.parse(os.path.join(ADDON_DIR, "addon.xml")).getroot()
    assert root.get("id") == "script.streamcinema.traktfix"
    points = {e.get("point") for e in root.iter("extension")}
    assert {"xbmc.python.script", "xbmc.service", "xbmc.addon.metadata"} <= points
    assert root.find(".//license").text.startswith("GPL-3.0")

    path = build_zip.build(ADDON_DIR, str(tmp_path))
    assert os.path.basename(path) == "script.streamcinema.traktfix-%s.zip" % root.get("version")
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        for name in patcher.ORIGINALS:
            member = "script.streamcinema.traktfix/resources/patch/" + name
            assert zf.read(member) == _read(PATCH_DIR, name)
    for rel in ("addon.xml", "default.py", "service.py", "context.py", "icon.png", "LICENSE.txt", "README.md",
                "resources/lib/patcher.py", "resources/lib/kodi.py"):
        assert "script.streamcinema.traktfix/" + rel in names
    assert not any("__pycache__" in n or n.endswith(".pyc") for n in names)


class _Tag(object):
    def __init__(self, mediatype, title, uids):
        self._m, self._t, self._u = mediatype, title, uids

    def getMediaType(self):
        return self._m

    def getTitle(self):
        return self._t

    def getUniqueID(self, key):
        return self._u.get(key, "")


class _ListItem(object):
    def __init__(self, tag):
        self._tag = tag

    def getVideoInfoTag(self):
        return self._tag

    def getLabel(self):
        return "label"


def _sc_params(url):
    """Dekódovanie parametrov ako kodiutils.params v Stream Cinema."""
    from urllib.parse import parse_qs, urlparse
    qs = parse_qs(urlparse(url).query)
    return {k: bytes.fromhex(v[0]).decode("utf-8") for k, v in qs.items()}


@pytest.mark.parametrize("mediatype,content", [("movie", "movie"), ("tvshow", "tvshow")])
def test_context_menu_runs_stream_cinema_manager(monkeypatch, mediatype, content):
    import sys
    import xbmc
    context = _load(os.path.join(ADDON_DIR, "context.py"), "traktfix_context")
    item = _ListItem(_Tag(mediatype, "Duna: Časť druhá", {"trakt": "4810", "imdb": "tt15239678"}))
    monkeypatch.setattr(sys, "listitem", item, raising=False)
    monkeypatch.setattr(xbmc, "BUILTINS", [])
    context.main()
    (cmd,) = xbmc.BUILTINS
    assert cmd.startswith("RunPlugin(plugin://plugin.video.stream-cinema/?") and cmd.endswith(")")
    # 4810 je platný hex; bez kódovania by ho Stream Cinema „dekódoval“ na nezmysel
    assert _sc_params(cmd[len("RunPlugin("):-1]) == {
        "action": "trakt.manager", "content": content, "title": "Duna: Časť druhá",
        "trakt": "4810", "imdb": "tt15239678"}


def test_context_menu_registered():
    root = ET.parse(os.path.join(ADDON_DIR, "addon.xml")).getroot()
    item = root.find("extension[@point='kodi.context.item']/menu/item")
    assert item.get("library") == "context.py"
    assert "plugin.video.stream-cinema" in item.find("visible").text
    # manager v opravenom Trakt.py, na ktorý kontextové menu volá
    assert b"action == 'trakt.manager'" in _read(PATCH_DIR, "Trakt.py")
