# -*- coding: utf-8 -*-
"""Vstupný bod doplnku plugin.video.stvr: router akcií.

URL má tvar plugin://plugin.video.stvr/?action=…&…
Akcie s priečinkom (do_root, do_show, …) končia endOfDirectory, akcie
z kontextového menu (wl_add, search_remove, …) sa volajú cez RunPlugin.
"""

import datetime
import os
import shutil
import sys
from urllib.parse import parse_qsl

import xbmcgui
import xbmcplugin
import xbmcvfs

from resources.lib import api, kodiutils as ku, listing, storage

USER_AGENT = ("Mozilla/5.0 (compatible; plugin.video.stvr/%s; "
              "+https://github.com/tvadovic/plugin.video.stvr)" % ku.ADDON_VERSION)

QUALITY_HEIGHTS = (0, 1080, 720, 480, 360)   # index = nastavenie max_quality
FILTER_PARAMS = api.FILTER_KEYS

# Akcie, ktoré nevytvárajú adresár (RunPlugin z kontextového menu / nastavení).
COMMAND_ACTIONS = {"wl_add", "wl_remove", "search_remove", "search_clear", "clear_cache"}


class Router(object):

    def __init__(self, argv):
        self.base_url = argv[0]
        self.handle = int(argv[1]) if len(argv) > 1 and argv[1].lstrip("-").isdigit() else -1
        self.params = dict(parse_qsl(argv[2].lstrip("?"))) if len(argv) > 2 else {}
        self.cache = storage.Cache(ku.profile_path("cache"))
        self.watch_later = storage.WatchLater(ku.profile_path("watch_later.json"))
        self.history = storage.SearchHistory(ku.profile_path("search_history.json"))
        self.client = api.Client(cache=self.cache,
                                 list_ttl=max(0, ku.setting_int("cache_ttl", 30)) * 60,
                                 user_agent=USER_AGENT)
        self.dir = listing.Directory(self.base_url, self.handle, self.watch_later)

    # ------------------------------------------------------------ dispatch

    def run(self):
        action = self.params.get("action", "root")
        handler = getattr(self, "do_" + action, None)
        if handler is None:
            ku.log("Neznáma akcia: %s" % action, ku.xbmc.LOGWARNING)
            return self._fail(action)
        try:
            handler()
        except api.GeoBlockedError as err:
            ku.log(err, ku.xbmc.LOGWARNING)
            ku.ok_dialog(ku.tr(30032))
            self._fail(action)
        except api.NotAvailableError as err:
            ku.log(err, ku.xbmc.LOGWARNING)
            ku.ok_dialog(ku.tr(30031))
            self._fail(action)
        except api.ApiError as err:
            ku.log(err, ku.xbmc.LOGERROR)
            ku.notify(ku.tr(30030), error=True)
            self._fail(action)

    def _fail(self, action):
        if action == "play":
            xbmcplugin.setResolvedUrl(self.handle, False, xbmcgui.ListItem(offscreen=True))
        elif action not in COMMAND_ACTIONS:
            self.dir.fail()

    def _filters(self):
        return dict((k, self.params[k]) for k in FILTER_PARAMS if self.params.get(k))

    def _page(self):
        try:
            return max(1, int(self.params.get("page", 1)))
        except ValueError:
            return 1

    # ------------------------------------------------------------ menu

    def do_root(self):
        d = self.dir
        d.add_folder(ku.tr(30000), d.url(action="genres"), icon="DefaultGenre.png")
        d.add_folder(ku.tr(30001), d.url(action="letters"), icon="DefaultMovieTitle.png")
        d.add_folder(ku.tr(30002), d.url(action="channels"), icon="DefaultTVShows.png")
        d.add_folder(ku.tr(30006), d.url(action="filter", content="kids"), icon="DefaultTags.png")
        d.add_folder(ku.tr(30007), d.url(action="filter", content="eu"), icon="DefaultTags.png")
        d.add_folder(ku.tr(30003), d.url(action="calendar"), icon="DefaultYear.png")
        d.add_folder(ku.tr(30004), d.url(action="search"), icon="DefaultAddonsSearch.png")
        d.add_folder(ku.tr(30005), d.url(action="watchlater"), icon="DefaultPlaylist.png")
        d.end()

    def do_genres(self):
        for genre in self.client.genres():
            self.dir.add_folder(genre["title"], self.dir.url(action="genre", path=genre["path"]),
                                icon="DefaultGenre.png")
        self.dir.end()

    def do_genre(self):
        """Žáner alebo podžáner: odkaz na podžánre + relácie (1. strana)."""
        path = self.params["path"]
        if self.client.section(path)["children"]:
            self.dir.add_folder(ku.tr(30010), self.dir.url(action="subgenres", path=path),
                                icon="DefaultGenre.png")
        self._add_shows(path, {}, 1)
        self.dir.end("tvshows")

    def do_subgenres(self):
        for child in self.client.section(self.params["path"])["children"]:
            self.dir.add_folder(child["title"], self.dir.url(action="genre", path=child["path"]),
                                icon="DefaultGenre.png")
        self.dir.end()

    def do_shows(self):
        self._add_shows(self.params["path"], self._filters(), self._page())
        self.dir.end("tvshows")

    def _add_shows(self, path, filters, page):
        shows, has_more = self.client.shows(path, filters, page)
        for show in shows:
            self.dir.add_show(show)
        if has_more:
            params = dict(action="shows", path=path, page=page + 1)
            params.update(filters)
            self.dir.add_folder(ku.tr(30012), self.dir.url(**params), icon="DefaultFolder.png")

    def do_letters(self):
        for value, label in api.LETTERS:
            self.dir.add_folder(label, self.dir.url(action="filter", l=value), icon="DefaultMovieTitle.png")
        self.dir.end()

    def do_channels(self):
        for value, label in api.CHANNELS:
            self.dir.add_folder(label, self.dir.url(action="filter", ch=value), icon="DefaultTVShows.png")
        self.dir.end()

    def do_filter(self):
        """Filter (písmeno, kanál, pre deti, …) → žánre, v ktorých niečo je."""
        filters = self._filters()
        groups = [g for g in self.client.filtered_groups(filters) if g["path"]]
        if len(groups) == 1:
            self._add_shows(groups[0]["path"], filters, 1)
            return self.dir.end("tvshows")
        if not groups:
            ku.notify(ku.tr(30024))
        for group in groups:
            params = dict(action="shows", path=group["path"])
            params.update(filters)
            image = group["shows"][0]["image"] if group["shows"] else None
            plot = ", ".join(s["title"] for s in group["shows"]) + (" …" if group["has_more"] else "")
            self.dir.add_folder(group["title"], self.dir.url(**params), image=image, plot=plot)
        self.dir.end()

    # ------------------------------------------------------------ kalendár

    def do_calendar(self):
        today = datetime.date.today()
        month = self.params.get("month") or today.strftime("%Y-%m")
        for day in self.client.calendar(month):
            self.dir.add_folder(listing.format_date(day, weekday=True),
                                self.dir.url(action="day", date=day), icon="DefaultYear.png")
        year, mon = (int(p) for p in month.split("-"))
        prev = "%04d-%02d" % ((year, mon - 1) if mon > 1 else (year - 1, 12))
        self.dir.add_folder(ku.tr(30014) % "%d/%s" % (int(prev[5:]), prev[:4]),
                            self.dir.url(action="calendar", month=prev), icon="DefaultFolder.png")
        self.dir.end(cache_to_disc=False)

    def do_day(self):
        episodes = self.client.day_episodes(self.params["date"])
        durations = self._durations(episodes)
        for ep in episodes:
            title = ep["name"] + (" – " + ep["subtitle"] if ep["subtitle"] else "")
            label = "%s  %s" % (ep["air"][11:16], title)
            # Položky dňa nemajú showId, len sériu; s=series vráti epizódy tej série.
            self.dir.add_episode(ep, show_title=ep["name"], show_id=ep["series"] or None,
                                 duration=durations.get(ep["id"], 0), label=label)
        self.dir.end("episodes")

    # ------------------------------------------------------------ relácia

    def do_show(self):
        show_id = self.params["id"]
        title = self.params.get("title", "")
        page = self._page()
        per_page = max(5, ku.setting_int("page_size", 30))
        episodes, has_more = self.client.episodes(show_id, page, per_page)
        durations = self._durations(episodes)
        for ep in episodes:
            self.dir.add_episode(ep, show_title=title or ep["name"], show_id=show_id,
                                 duration=durations.get(ep["id"], 0), link_show=False)
        if has_more:
            self.dir.add_folder(ku.tr(30013), self.dir.url(action="show", id=show_id, title=title,
                                                            page=page + 1), icon="DefaultFolder.png")
        if not episodes and page == 1:
            ku.notify(ku.tr(30023))
        self.dir.end("episodes")

    def _durations(self, episodes):
        if not ku.setting_bool("fetch_duration", True):
            return {}
        return self.client.durations(ep["id"] for ep in episodes)

    # ------------------------------------------------------------ prehrávanie

    def do_play(self):
        episode_id = self.params["id"]
        info = self.client.stream(episode_id)   # vždy čerstvo, nikdy z cache
        use_isa = ku.setting_bool("use_isa") and ku.has_addon("inputstream.adaptive")
        manifest = "hls"
        if use_isa and ku.setting_int("isa_manifest") == 1 and info["dash"]:
            path, manifest = info["dash"], "mpd"
        else:
            path = info["hls"]
        if not path:
            raise api.NotAvailableError("Chýba HLS stream pre %s" % episode_id)

        max_height = QUALITY_HEIGHTS[min(max(ku.setting_int("max_quality"), 0), len(QUALITY_HEIGHTS) - 1)]
        if max_height and manifest == "hls":
            try:
                variant = api.pick_variant(self.client.hls_variants(path), max_height)
                if variant:
                    path = variant["url"]
                    ku.log("Variant %sp: %s" % (variant["height"], path))
            except api.ApiError as err:
                ku.log("Master playlist sa nepodarilo načítať, hrám master: %s" % err)

        subtitles = self._subtitles(episode_id, info["subtitles"]) if ku.setting_bool("subtitles", True) else []
        listing.resolve(self.handle, path, info, use_isa=use_isa, manifest=manifest, subtitles=subtitles)

    def _subtitles(self, episode_id, tracks):
        """Stiahne WebVTT do dočasného súboru {id}.{jazyk}.vtt, aby Kodi poznalo jazyk."""
        folder = xbmcvfs.translatePath("special://temp/%s/" % ku.ADDON_ID)
        shutil.rmtree(folder, ignore_errors=True)
        files = []
        for track in tracks:
            try:
                text = self.client.fetch(track["src"])
            except api.ApiError as err:
                ku.log("Titulky sa nepodarilo stiahnuť: %s" % err)
                continue
            if not os.path.isdir(folder):
                os.makedirs(folder)
            name = os.path.join(folder, "%s.%s.vtt" % (episode_id, track["lang"] or "sk"))
            with open(name, "w", encoding="utf-8") as f:
                f.write(text)
            files.append(name)
        return files

    # ------------------------------------------------------------ hľadanie

    def do_search(self):
        d = self.dir
        d.add_folder(ku.tr(30015), d.url(action="search_new"), icon="DefaultAddonsSearch.png")
        clear = (ku.tr(30018), "RunPlugin(%s)" % d.url(action="search_clear"))
        for query in self.history.items():
            d.add_folder(query, d.url(action="search_results", q=query), icon="DefaultAddonsSearch.png",
                         context=[(ku.tr(30017), "RunPlugin(%s)" % d.url(action="search_remove", q=query)),
                                  clear])
        d.end(cache_to_disc=False)

    def do_search_new(self):
        query = ku.keyboard(ku.tr(30016))
        if query is None:
            return self.dir.fail()
        if len(query) < 3:
            ku.notify(ku.tr(30034))
            return self.dir.fail()
        self.history.add(query)
        # Nahradí položku „nové hľadanie“ výsledkami, aby návrat späť znova neotváral klávesnicu.
        self.dir.fail()
        ku.builtin("Container.Update(%s,replace)" % self.dir.url(action="search_results", q=query))

    def do_search_results(self):
        query = self.params["q"]
        try:
            offset = int(self.params.get("offset", 0))
        except ValueError:
            offset = 0
        shows, _, next_offset = self.client.search(query, offset)
        if not shows and not offset:
            ku.notify(ku.tr(30024))
        for show in shows:
            self.dir.add_show(show)
        if next_offset:
            self.dir.add_folder(ku.tr(30012), self.dir.url(action="search_results", q=query, offset=next_offset),
                                icon="DefaultFolder.png")
        self.dir.end("tvshows")

    def do_search_remove(self):
        self.history.remove(self.params.get("q", ""))
        ku.builtin("Container.Refresh")

    def do_search_clear(self):
        self.history.clear()
        ku.builtin("Container.Refresh")

    # ------------------------------------------------------------ pozrieť neskôr

    def do_watchlater(self):
        items = self.watch_later.items()
        if not items:
            ku.notify(ku.tr(30023))
        for item in items:
            if item["kind"] == "show":
                self.dir.add_show({"id": item["id"], "title": item.get("title"),
                                   "image": item.get("image"), "plot": item.get("plot")})
            else:
                show_title = item.get("show_title") or item.get("title") or ""
                label = "%s – %s" % (show_title, listing.format_date(item.get("date", "")))
                if item.get("title") and item["title"] != show_title:
                    label += ": " + item["title"]
                ep = {"id": item["id"], "name": item.get("title") or show_title, "subtitle": "",
                      "date": item.get("date", ""), "plot": item.get("plot", ""), "image": item.get("image", "")}
                self.dir.add_episode(ep, show_title=show_title, show_id=item.get("show_id") or None,
                                     label=label)
        self.dir.end("videos", cache_to_disc=False)

    def do_wl_add(self):
        p = self.params
        self.watch_later.add(p["kind"], p["id"], **dict((k, p.get(k, "")) for k in storage.WatchLater.FIELDS))
        ku.notify(ku.tr(30021))
        ku.builtin("Container.Refresh")

    def do_wl_remove(self):
        self.watch_later.remove(self.params["kind"], self.params["id"])
        ku.notify(ku.tr(30022))
        ku.builtin("Container.Refresh")

    # ------------------------------------------------------------ nastavenia

    def do_clear_cache(self):
        self.cache.clear()
        ku.notify(ku.tr(30033))


if __name__ == "__main__":
    Router(sys.argv).run()
