# -*- coding: utf-8 -*-
"""Zabalí doplnok do dist/{addon_id}-{verzia}.zip.

ZIP obsahuje priečinok {addon_id}/ (tak ho očakáva Kodi pri inštalácii zo ZIP).
Hlavný doplnok (koreň repozitára) sa balí bez testov, dev nástrojov a dokumentácie;
iný doplnok (napr. repository.tvadovic/) sa balí celý.

    python dev/build_zip.py                          # plugin.video.stvr, verzia z addon.xml
    python dev/build_zip.py --check v0.1.0           # overí, že tag sedí s verziou v addon.xml
    python dev/build_zip.py --addon repository.tvadovic   # zabalí repozitár doplnkov
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INCLUDE = ["addon.xml", "main.py", "icon.png", "fanart.jpg", "LICENSE.txt", "resources"]
SKIP_DIRS = {"__pycache__"}
SKIP_EXT = {".pyc", ".pyo"}


def addon_info(addon_dir=ROOT):
    tree = ET.parse(os.path.join(addon_dir, "addon.xml")).getroot()
    return tree.get("id"), tree.get("version")


def iter_files(addon_dir=ROOT):
    include = INCLUDE if os.path.abspath(addon_dir) == ROOT else sorted(os.listdir(addon_dir))
    for entry in include:
        path = os.path.join(addon_dir, entry)
        if os.path.isfile(path):
            if os.path.splitext(entry)[1] not in SKIP_EXT:
                yield entry
            continue
        if entry in SKIP_DIRS:
            continue
        for folder, dirs, files in os.walk(path):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            for name in sorted(files):
                if os.path.splitext(name)[1] not in SKIP_EXT:
                    yield os.path.relpath(os.path.join(folder, name), addon_dir).replace(os.sep, "/")


def build(addon_dir=ROOT, out=os.path.join(ROOT, "dist")):
    """Zabalí doplnok z addon_dir a vráti cestu k ZIP-u."""
    addon_id, version = addon_info(addon_dir)
    os.makedirs(out, exist_ok=True)
    target = os.path.join(out, "%s-%s.zip" % (addon_id, version))
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in iter_files(addon_dir):
            zf.write(os.path.join(addon_dir, rel), "%s/%s" % (addon_id, rel))
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", metavar="TAG", help="overí, že tag (v1.2.3) zodpovedá verzii v addon.xml")
    parser.add_argument("--addon", metavar="DIR", default=ROOT,
                        help="priečinok doplnku s addon.xml (predvolene koreň = plugin.video.stvr)")
    parser.add_argument("--out", default=os.path.join(ROOT, "dist"))
    args = parser.parse_args()

    addon_dir = os.path.abspath(args.addon)
    if args.check and args.check.lstrip("v") != addon_info(addon_dir)[1]:
        sys.exit("Tag %s nezodpovedá verzii %s v addon.xml" % (args.check, addon_info(addon_dir)[1]))
    print(build(addon_dir, args.out))


if __name__ == "__main__":
    main()
