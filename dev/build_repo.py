# -*- coding: utf-8 -*-
"""Poskladá Kodi repozitár doplnkov (obsah vetvy gh-pages) zo ZIP-ov doplnkov.

    python dev/build_zip.py
    python dev/build_zip.py --addon repository.tvadovic
    python dev/build_repo.py dist/*.zip --out ../gh-pages

Výstup (--out, typicky checkout vetvy gh-pages):

    addons.xml, addons.xml.md5        # najnovšia verzia každého doplnku
    {addon_id}/{addon_id}-{verzia}.zip
    {addon_id}/icon.png, fanart.jpg   # assety z addon.xml najnovšej verzie
    repository.*-{verzia}.zip         # kópia najnovšieho repozitára v koreni (ľahká inštalácia)
    index.html                        # v každom priečinku, HTTP listing pre Kodi „Pridať zdroj“
    .nojekyll

ZIP-y, ktoré už vo výstupe sú (staršie verzie), zostanú; addons.xml sa skladá zo všetkých.
Existujúci ZIP rovnakej verzie sa neprepisuje (bez --force), zverejnená verzia sa nemá meniť.
"""

import argparse
import hashlib
import html
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile
from urllib.parse import quote

ASSET_TAGS = ("icon", "fanart", "banner", "clearlogo", "poster", "screenshot")
XML_DECL = re.compile(r"^\s*<\?xml[^>]*\?>\s*")
SOURCE_URL = "https://github.com/tvadovic/plugin.video.stvr"


def version_key(version):
    """Kľúč na porovnanie verzií Kodi: 1.2.10 > 1.2.9, 1.0.0~beta1 < 1.0.0."""
    main, _, tag = version.partition("~")
    nums = []
    for part in main.split("."):
        digits = re.match(r"\d*", part).group()
        nums.append(int(digits) if digits else 0)
    return tuple(nums), tag == "", tag


def read_addon(zip_path):
    """Vráti (id, verzia, text addon.xml) zo ZIP-u a overí jeho štruktúru {id}/..."""
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        xml_names = [n for n in names if n.count("/") == 1 and n.endswith("/addon.xml")]
        if len(xml_names) != 1:
            raise ValueError("%s: chýba {addon_id}/addon.xml" % zip_path)
        text = zf.read(xml_names[0]).decode("utf-8")
    root = ET.fromstring(text.encode("utf-8"))
    addon_id, version = root.get("id"), root.get("version")
    if not addon_id or not version:
        raise ValueError("%s: addon.xml nemá id alebo version" % zip_path)
    folder = xml_names[0].split("/")[0]
    if folder != addon_id:
        raise ValueError("%s: priečinok %s/ nezodpovedá id %s" % (zip_path, folder, addon_id))
    stray = [n for n in names if not n.startswith(addon_id + "/")]
    if stray:
        raise ValueError("%s: súbory mimo %s/: %s" % (zip_path, addon_id, ", ".join(stray[:3])))
    return addon_id, version, text


def asset_paths(addon_xml):
    root = ET.fromstring(addon_xml.encode("utf-8"))
    paths = []
    for ext in root.iter("extension"):
        if ext.get("point") != "xbmc.addon.metadata":
            continue
        for assets in ext.iter("assets"):
            for child in assets:
                if child.tag in ASSET_TAGS and child.text and child.text.strip():
                    paths.append(child.text.strip())
    return paths


def add_zip(zip_path, out, force=False):
    """Skopíruje ZIP do out/{id}/{id}-{verzia}.zip. Vráti cieľovú cestu."""
    addon_id, version, _ = read_addon(zip_path)
    target = os.path.join(out, addon_id, "%s-%s.zip" % (addon_id, version))
    os.makedirs(os.path.dirname(target), exist_ok=True)
    if os.path.exists(target) and not force:
        if not same_file(zip_path, target):
            print("Ponechávam existujúci %s (iný obsah, použite --force)" % target, file=sys.stderr)
        return target
    shutil.copyfile(zip_path, target)
    return target


def same_file(a, b):
    with open(a, "rb") as fa, open(b, "rb") as fb:
        return fa.read() == fb.read()


def find_addons(out):
    """{addon_id: [(verzia, cesta), ...]} zo všetkých ZIP-ov out/{id}/{id}-*.zip."""
    found = {}
    for addon_id in sorted(os.listdir(out)):
        folder = os.path.join(out, addon_id)
        if addon_id.startswith(".") or not os.path.isdir(folder):
            continue
        prefix = addon_id + "-"
        for name in os.listdir(folder):
            if name.startswith(prefix) and name.endswith(".zip"):
                version = name[len(prefix):-len(".zip")]
                found.setdefault(addon_id, []).append((version, os.path.join(folder, name)))
    return found


def extract_assets(zip_path, addon_id, addon_xml, out):
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        for rel in asset_paths(addon_xml):
            member = "%s/%s" % (addon_id, rel)
            if member not in names:
                print("%s: asset %s chýba" % (zip_path, rel), file=sys.stderr)
                continue
            target = os.path.join(out, addon_id, *rel.split("/"))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with zf.open(member) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)


def write_addons_xml(out, addon_xmls):
    body = "\n".join(XML_DECL.sub("", text).strip() for text in addon_xmls)
    data = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n%s\n</addons>\n'
            % body).encode("utf-8")
    ET.fromstring(data)  # musí byť platné XML
    with open(os.path.join(out, "addons.xml"), "wb") as f:
        f.write(data)
    digest = hashlib.md5(data).hexdigest()
    with open(os.path.join(out, "addons.xml.md5"), "wb") as f:
        f.write(digest.encode("ascii"))
    return digest


def sync_root_zips(out, latest):
    """Najnovší ZIP každého repository.* doplnku aj v koreni, staršie kópie preč."""
    for addon_id, (version, path) in latest.items():
        if not addon_id.startswith("repository."):
            continue
        keep = os.path.basename(path)
        for name in os.listdir(out):
            if name.startswith(addon_id + "-") and name.endswith(".zip") and name != keep:
                os.remove(os.path.join(out, name))
        shutil.copyfile(path, os.path.join(out, keep))


def index_html(title, dirs, files, intro=""):
    # Kodi berie z HTML listingu len odkazy, ktorých text = href (ostatné ignoruje).
    links = ['<li><a href="%s">%s</a></li>' % (quote(n), html.escape(n))
             for n in [d + "/" for d in dirs] + files]
    return ("<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"utf-8\">\n"
            "<title>%s</title>\n</head>\n<body>\n<h1>%s</h1>\n%s<ul>\n%s\n</ul>\n</body>\n</html>\n"
            % (html.escape(title), html.escape(title), intro, "\n".join(links)))


def write_indexes(out):
    intro = ('<p>Kodi repozitár doplnkov. V Kodi pridajte túto adresu ako zdroj a nainštalujte '
             '<code>repository.*.zip</code>. Návod: <a href="%s#readme">GitHub</a>.</p>\n' % SOURCE_URL)
    for folder, dirs, files in os.walk(out):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        names = sorted(f for f in files if f != "index.html" and not f.startswith("."))
        rel = os.path.relpath(folder, out).replace(os.sep, "/")
        title = "/" if rel == "." else "/%s/" % rel
        page = index_html(title, dirs, names, intro if rel == "." else "")
        with open(os.path.join(folder, "index.html"), "w", encoding="utf-8", newline="\n") as f:
            f.write(page)


def build_repo(zips, out, force=False):
    """Pridá ZIP-y do out a pregeneruje addons.xml, md5, assety a index.html.

    Vráti {addon_id: najnovšia verzia}.
    """
    os.makedirs(out, exist_ok=True)
    for path in zips:
        add_zip(path, out, force)
    latest, addon_xmls = {}, []
    for addon_id, versions in sorted(find_addons(out).items()):
        version, path = max(versions, key=lambda v: version_key(v[0]))
        zip_id, zip_version, text = read_addon(path)
        if (zip_id, zip_version) != (addon_id, version):
            raise ValueError("%s: obsahuje %s %s" % (path, zip_id, zip_version))
        extract_assets(path, addon_id, text, out)
        latest[addon_id] = (version, path)
        addon_xmls.append(text)
    if not addon_xmls:
        raise ValueError("Žiadne doplnky v %s" % out)
    write_addons_xml(out, addon_xmls)
    sync_root_zips(out, latest)
    open(os.path.join(out, ".nojekyll"), "w").close()
    write_indexes(out)
    return {addon_id: version for addon_id, (version, _) in latest.items()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("zips", nargs="*", help="ZIP-y doplnkov z dev/build_zip.py")
    parser.add_argument("--out", required=True, help="výstupný priečinok (checkout vetvy gh-pages)")
    parser.add_argument("--force", action="store_true", help="prepísať existujúci ZIP rovnakej verzie")
    args = parser.parse_args(argv)
    for addon_id, version in sorted(build_repo(args.zips, args.out, args.force).items()):
        print("%s %s" % (addon_id, version))


if __name__ == "__main__":
    main()
