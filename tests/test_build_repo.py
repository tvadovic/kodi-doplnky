# -*- coding: utf-8 -*-
"""Testy balenia ZIP (dev/build_zip.py) a generátora Kodi repozitára (dev/build_repo.py)."""
import hashlib
import importlib.util
import os
import re
import xml.etree.ElementTree as ET
import zipfile

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STVR_DIR = os.path.join(ROOT, "plugin.video.stvr")
REPO_DIR = os.path.join(ROOT, "repository.tvadovic")
PAGES_URL = "https://tvadovic.github.io/kodi-doplnky/"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "dev", name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_zip = _load("build_zip")
build_repo = _load("build_repo")


def _fake_zip(folder, addon_id, version, extra=None, top=None):
    """Minimálny ZIP doplnku s ikonou; top = iný názov priečinka v ZIP-e."""
    path = os.path.join(str(folder), "%s-%s.zip" % (addon_id, version))
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<addon id="%s" version="%s" name="x">'
           '<extension point="xbmc.addon.metadata"><assets><icon>icon.png</icon></assets>'
           '</extension></addon>' % (addon_id, version))
    top = top or addon_id
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(top + "/addon.xml", xml)
        zf.writestr(top + "/icon.png", b"PNG-" + version.encode())
        for name, data in (extra or {}).items():
            zf.writestr(name, data)
    return path


@pytest.fixture
def zips(tmp_path):
    dist = str(tmp_path / "dist")
    return [build_zip.build(STVR_DIR, dist), build_zip.build(REPO_DIR, dist)]


def test_build_zip_plugin_and_repository(zips):
    plugin, repo = zips
    pid, pver = build_zip.addon_info(STVR_DIR)
    assert os.path.basename(plugin) == "%s-%s.zip" % (pid, pver)
    with zipfile.ZipFile(plugin) as zf:
        names = zf.namelist()
    assert all(n.startswith(pid + "/") for n in names)
    assert pid + "/main.py" in names
    assert not any("/tests/" in n or "/dev/" in n or n.endswith(".pyc") for n in names)

    with zipfile.ZipFile(repo) as zf:
        names = sorted(zf.namelist())
    assert names == ["repository.tvadovic/addon.xml", "repository.tvadovic/icon.png"]


def test_repository_addon_xml_points_to_pages():
    root = ET.parse(os.path.join(REPO_DIR, "addon.xml")).getroot()
    assert (root.get("id"), root.get("version")) == ("repository.tvadovic", "1.0.2")
    d = root.find("extension[@point='xbmc.addon.repository']/dir")
    assert d.find("info").text == PAGES_URL + "addons.xml"
    assert d.find("info").get("compressed") == "false"
    assert d.find("checksum").text == PAGES_URL + "addons.xml.md5"
    assert d.find("datadir").text == PAGES_URL
    assert d.find("datadir").get("zip") == "true"


def test_build_repo_layout(tmp_path, zips):
    out = str(tmp_path / "pages")
    latest = build_repo.build_repo(zips, out)
    pid, pver = build_zip.addon_info(STVR_DIR)
    assert latest == {pid: pver, "repository.tvadovic": "1.0.2"}

    for addon_id, version in latest.items():
        assert os.path.isfile(os.path.join(out, addon_id, "%s-%s.zip" % (addon_id, version)))
        assert os.path.isfile(os.path.join(out, addon_id, "icon.png"))
    assert os.path.isfile(os.path.join(out, pid, "fanart.jpg"))
    assert os.path.isfile(os.path.join(out, "repository.tvadovic-1.0.2.zip"))
    assert os.path.isfile(os.path.join(out, ".nojekyll"))

    with open(os.path.join(out, "addons.xml"), "rb") as f:
        data = f.read()
    with open(os.path.join(out, "addons.xml.md5")) as f:
        assert f.read() == hashlib.md5(data).hexdigest()
    root = ET.fromstring(data)
    assert root.tag == "addons"
    assert {(a.get("id"), a.get("version")) for a in root.findall("addon")} == set(latest.items())
    assert data.count(b"<?xml") == 1


def test_index_html_links_match_text(tmp_path, zips):
    out = str(tmp_path / "pages")
    build_repo.build_repo(zips, out)
    link = re.compile(r'<a href="([^"]+)">([^<]+)</a>')

    def kodi_links(folder):
        with open(os.path.join(out, folder, "index.html"), encoding="utf-8") as f:
            # Kodi berie len odkazy, kde text = href
            return [h for h, t in link.findall(f.read()) if h == t]

    root_links = kodi_links("")
    for name in ("addons.xml", "addons.xml.md5", "repository.tvadovic/",
                 "plugin.video.stvr/", "repository.tvadovic-1.0.2.zip"):
        assert name in root_links
    assert "index.html" not in root_links
    assert "repository.tvadovic-1.0.2.zip" in kodi_links("repository.tvadovic")


def test_build_repo_keeps_old_zips_and_picks_newest(tmp_path):
    src, out = tmp_path / "src", str(tmp_path / "pages")
    src.mkdir()
    build_repo.build_repo([_fake_zip(src, "plugin.video.x", "0.9.0"),
                           _fake_zip(src, "repository.x", "1.0.0")], out)
    # ďalší release: len nová verzia pluginu, repozitár a stará verzia už vo výstupe sú
    latest = build_repo.build_repo([_fake_zip(src, "plugin.video.x", "0.10.0")], out)
    assert latest == {"plugin.video.x": "0.10.0", "repository.x": "1.0.0"}
    assert sorted(os.listdir(os.path.join(out, "plugin.video.x"))) == [
        "icon.png", "index.html", "plugin.video.x-0.10.0.zip", "plugin.video.x-0.9.0.zip"]
    with open(os.path.join(out, "plugin.video.x", "icon.png"), "rb") as f:
        assert f.read() == b"PNG-0.10.0"
    with open(os.path.join(out, "addons.xml"), encoding="utf-8") as f:
        assert 'version="0.10.0"' in f.read()

    # nová verzia repozitára nahradí kópiu v koreni
    build_repo.build_repo([_fake_zip(src, "repository.x", "1.1.0")], out)
    root_zips = sorted(n for n in os.listdir(out) if n.endswith(".zip"))
    assert root_zips == ["repository.x-1.1.0.zip"]


def test_build_repo_does_not_overwrite_published_zip(tmp_path):
    out = str(tmp_path / "pages")
    first, second = tmp_path / "a", tmp_path / "b"
    first.mkdir()
    second.mkdir()
    build_repo.build_repo([_fake_zip(first, "plugin.video.x", "1.0.0")], out)
    changed = _fake_zip(second, "plugin.video.x", "1.0.0", extra={"plugin.video.x/new.txt": "x"})
    target = os.path.join(out, "plugin.video.x", "plugin.video.x-1.0.0.zip")

    def names():
        with zipfile.ZipFile(target) as zf:
            return zf.namelist()

    build_repo.build_repo([changed], out)
    assert "plugin.video.x/new.txt" not in names()
    build_repo.build_repo([changed], out, force=True)
    assert "plugin.video.x/new.txt" in names()


@pytest.mark.parametrize("kwargs", [
    {"top": "wrong.folder"},
    {"extra": {"stray.txt": "x"}},
])
def test_build_repo_rejects_bad_zip_structure(tmp_path, kwargs):
    bad = _fake_zip(tmp_path, "plugin.video.x", "1.0.0", **kwargs)
    with pytest.raises(ValueError):
        build_repo.build_repo([bad], str(tmp_path / "pages"))


@pytest.mark.parametrize("older, newer", [
    ("0.9.0", "0.10.0"),
    ("1.0.0~beta1", "1.0.0"),
    ("1.0", "1.0.1"),
    ("1.2.3", "2.0.0"),
])
def test_version_key(older, newer):
    assert build_repo.version_key(older) < build_repo.version_key(newer)


def test_addon_dirs_finds_all_addons():
    ids = sorted(build_zip.addon_info(d)[0] for d in build_zip.addon_dirs())
    assert ids == ["plugin.video.stvr", "repository.tvadovic", "script.streamcinema.traktfix"]


def test_build_zip_skips_dev_folders(tmp_path):
    with zipfile.ZipFile(build_zip.build(STVR_DIR, str(tmp_path))) as zf:
        names = zf.namelist()
    assert "plugin.video.stvr/README.md" in names
    assert not any("/docs/" in n or "/tests/" in n for n in names)
