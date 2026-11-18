# -*- coding: utf-8 -*-
"""Spustí router doplnku mimo Kodi a vypíše výsledok.

Príklady:
    python dev/run.py
    python dev/run.py "plugin://plugin.video.stvr/?action=genres"
    python dev/run.py "?action=show&id=14126&title=Duel"
    python dev/run.py "?action=play&id=630571" --set max_quality=2
    python dev/run.py "?action=search_new" --input duel
    python dev/run.py "?action=genres" --lang en -v

Dáta (cache, Pozrieť neskôr, história) sa ukladajú do dev/profile/.
"""

import argparse
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path[:0] = [ROOT, os.path.join(ROOT, "dev", "stubs")]

BASE_URL = "plugin://plugin.video.stvr/"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url", nargs="?", default=BASE_URL, help="plugin:// URL alebo len ?query")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="prepíše nastavenie")
    parser.add_argument("--input", action="append", default=[], help="text pre klávesnicu (hľadanie)")
    parser.add_argument("--lang", choices=("sk", "en"), default="sk")
    parser.add_argument("--details", action="store_true", help="vypíše aj popis, obrázok a kontextové menu")
    parser.add_argument("-v", "--verbose", action="store_true", help="vypíše debug log")
    args = parser.parse_args()

    if args.lang == "en":
        os.environ["KODI_LANG"] = "en"
    if args.verbose:
        os.environ["STVR_DEBUG"] = "1"
    for line in (sys.stdout, sys.stderr):
        line.reconfigure(encoding="utf-8")

    import xbmc
    import xbmcaddon
    import xbmcplugin
    for item in args.set:
        key, _, value = item.partition("=")
        xbmcaddon.SETTINGS[key] = value
    xbmc.KEYBOARD_INPUT.extend(args.input)

    query = args.url.split("?", 1)[1] if "?" in args.url else ""
    import main as addon_main
    started = time.time()
    addon_main.Router([BASE_URL, "1", "?" + query]).run()
    elapsed = time.time() - started

    for url, li, is_folder in xbmcplugin.ITEMS:
        kind = "D" if is_folder else ("P" if li.getProperty("IsPlayable") == "true" else "-")
        print("[%s] %s\n      %s" % (kind, li.getLabel(), url))
        if args.details:
            info = li.getVideoInfoTag().info
            for key in ("plot", "duration", "firstaired"):
                if info.get(key):
                    print("      %s: %s" % (key, str(info[key]).replace("\n", " ")[:120]))
            if li.art.get("thumb"):
                print("      thumb: %s" % li.art["thumb"])
            for label, command in li.context:
                print("      menu: %s -> %s" % (label, command[:100]))
    resolved = xbmcplugin.STATE.get("resolved")
    if resolved:
        ok, li = resolved
        print("[resolved] ok=%s mime=%s\n  path: %s" % (ok, li.mimetype, li.getPath()))
        for key, value in li.properties.items():
            print("  property %s=%s" % (key, value))
        for sub in li.subtitles:
            print("  subtitle: %s" % sub)
    print("-- %d položiek, content=%s, succeeded=%s, %.2f s" % (
        len(xbmcplugin.ITEMS), xbmcplugin.STATE.get("content", ""),
        xbmcplugin.STATE.get("succeeded", "-"), elapsed))


if __name__ == "__main__":
    main()
