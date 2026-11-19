# -*- coding: utf-8 -*-
"""Zabalí doplnok do dist/{addon_id}-{verzia}.zip.

Každý doplnok je priečinok s addon.xml v koreni repozitára (plugin.video.stvr/,
script.streamcinema.traktfix/, repository.tvadovic/). ZIP obsahuje priečinok
{addon_id}/ (tak ho očakáva Kodi pri inštalácii zo ZIP); vývojové súbory
(docs/, tests/, __pycache__) sa nebalia.

    python dev/build_zip.py                                   # plugin.video.stvr
    python dev/build_zip.py --addon script.streamcinema.traktfix
    python dev/build_zip.py --all                             # všetky doplnky, cesta na riadok
"""

import argparse
import os
import xml.etree.ElementTree as ET
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_ADDON = os.path.join(ROOT, "plugin.video.stvr")
SKIP_DIRS = {"__pycache__", "docs", "tests"}
SKIP_EXT = {".pyc", ".pyo"}


def addon_dirs(root=ROOT):
    """Priečinky doplnkov v koreni repozitára (majú addon.xml)."""
    return [os.path.join(root, d) for d in sorted(os.listdir(root))
            if not d.startswith(".") and os.path.isfile(os.path.join(root, d, "addon.xml"))]


def addon_info(addon_dir=DEFAULT_ADDON):
    tree = ET.parse(os.path.join(addon_dir, "addon.xml")).getroot()
    return tree.get("id"), tree.get("version")


def iter_files(addon_dir=DEFAULT_ADDON):
    for folder, dirs, files in os.walk(addon_dir):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            if os.path.splitext(name)[1] not in SKIP_EXT:
                yield os.path.relpath(os.path.join(folder, name), addon_dir).replace(os.sep, "/")


def build(addon_dir=DEFAULT_ADDON, out=os.path.join(ROOT, "dist")):
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
    parser.add_argument("--addon", metavar="DIR", default=DEFAULT_ADDON,
                        help="priečinok doplnku s addon.xml (predvolene plugin.video.stvr)")
    parser.add_argument("--all", action="store_true", help="zabalí všetky doplnky v repozitári")
    parser.add_argument("--out", default=os.path.join(ROOT, "dist"))
    args = parser.parse_args()

    for addon_dir in addon_dirs() if args.all else [os.path.abspath(args.addon)]:
        print(build(addon_dir, args.out))


if __name__ == "__main__":
    main()
