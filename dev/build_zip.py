# -*- coding: utf-8 -*-
"""Zabalí doplnok do dist/plugin.video.stvr-{verzia}.zip.

ZIP obsahuje priečinok plugin.video.stvr/ (tak ho očakáva Kodi pri inštalácii zo ZIP).
Do balíka idú len súbory potrebné v Kodi, bez testov, dev nástrojov a dokumentácie.

    python dev/build_zip.py            # verzia z addon.xml
    python dev/build_zip.py --check v0.1.0   # overí, že tag sedí s verziou v addon.xml
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


def addon_info():
    tree = ET.parse(os.path.join(ROOT, "addon.xml")).getroot()
    return tree.get("id"), tree.get("version")


def iter_files():
    for entry in INCLUDE:
        path = os.path.join(ROOT, entry)
        if os.path.isfile(path):
            yield entry
            continue
        for folder, dirs, files in os.walk(path):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            for name in sorted(files):
                if os.path.splitext(name)[1] not in SKIP_EXT:
                    yield os.path.relpath(os.path.join(folder, name), ROOT).replace(os.sep, "/")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", metavar="TAG", help="overí, že tag (v1.2.3) zodpovedá verzii v addon.xml")
    parser.add_argument("--out", default=os.path.join(ROOT, "dist"))
    args = parser.parse_args()

    addon_id, version = addon_info()
    if args.check and args.check.lstrip("v") != version:
        sys.exit("Tag %s nezodpovedá verzii %s v addon.xml" % (args.check, version))

    os.makedirs(args.out, exist_ok=True)
    target = os.path.join(args.out, "%s-%s.zip" % (addon_id, version))
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in iter_files():
            zf.write(os.path.join(ROOT, rel), "%s/%s" % (addon_id, rel))
    print(target)


if __name__ == "__main__":
    main()
