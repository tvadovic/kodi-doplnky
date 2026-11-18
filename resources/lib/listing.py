# -*- coding: utf-8 -*-
"""Tvorba položiek Kodi adresára (ListItem) pre relácie, epizódy a priečinky."""

from urllib.parse import urlencode

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib import kodiutils as ku

WEEKDAYS = (30200, 30201, 30202, 30203, 30204, 30205, 30206)


def format_date(iso_date, weekday=False):
    """'2026-11-17' → '17.11.2026' (voliteľne s dňom v týždni)."""
    try:
        y, m, d = (int(p) for p in iso_date[:10].split("-"))
    except ValueError:
        return iso_date
    text = "%d.%d.%d" % (d, m, y)
    if weekday:
        import datetime
        text = "%s %s" % (ku.tr(WEEKDAYS[datetime.date(y, m, d).weekday()]), text)
    return text


def _set_art(li, art):
    """setArt bez prázdnych hodnôt (Kodi neprijme None)."""
    li.setArt(dict((k, v) for k, v in art.items() if v))


class Directory(object):
    """Jeden výpis adresára doplnku."""

    def __init__(self, base_url, handle, watch_later=None):
        self.base_url = base_url
        self.handle = handle
        self.watch_later = watch_later

    # --- URL

    def url(self, **params):
        """plugin://plugin.video.stvr/?action=…; poradie parametrov je stabilné."""
        clean = [(k, v) for k, v in params.items() if v not in (None, "")]
        return self.base_url + "?" + urlencode(clean)

    def play_url(self, episode_id):
        # Stabilná URL: Kodi podľa nej pamätá pozíciu a „pozreté“.
        return self.url(action="play", id=episode_id)

    # --- kontextové menu „Pozrieť neskôr“

    def _watch_later_menu(self, kind, item_id, info):
        if self.watch_later is None:
            return []
        if self.watch_later.contains(kind, item_id):
            return [(ku.tr(30020),
                     "RunPlugin(%s)" % self.url(action="wl_remove", kind=kind, id=item_id))]
        params = dict(action="wl_add", kind=kind, id=item_id)
        params.update((k, (info.get(k) or "")[:400]) for k in
                      ("title", "image", "plot", "show_id", "show_title", "date"))
        return [(ku.tr(30019), "RunPlugin(%s)" % self.url(**params))]

    # --- položky

    def add_folder(self, label, url, icon=None, image=None, plot=None, context=None):
        li = xbmcgui.ListItem(label, offscreen=True)
        art = {"icon": icon or image or ku.ADDON_ICON, "fanart": ku.ADDON_FANART}
        if image:
            art.update(thumb=image, fanart=image)
        elif icon:
            art["thumb"] = icon
        _set_art(li, art)
        if plot:
            li.getVideoInfoTag().setPlot(plot)
        if context:
            li.addContextMenuItems(context)
        xbmcplugin.addDirectoryItem(self.handle, url, li, isFolder=True)

    def add_show(self, show, extra_context=None):
        """Relácia → priečinok s epizódami."""
        url = self.url(action="show", id=show["id"], title=show.get("title"))
        li = xbmcgui.ListItem(show.get("title") or show["id"], offscreen=True)
        image = show.get("image")
        _set_art(li, {"thumb": image, "icon": image, "landscape": image, "fanart": image or ku.ADDON_FANART})
        tag = li.getVideoInfoTag()
        tag.setMediaType("tvshow")
        tag.setTitle(show.get("title") or "")
        if show.get("plot"):
            tag.setPlot(show["plot"])
        context = self._watch_later_menu("show", show["id"], {
            "title": show.get("title"), "image": image, "plot": show.get("plot")})
        li.addContextMenuItems(context + (extra_context or []))
        xbmcplugin.addDirectoryItem(self.handle, url, li, isFolder=True)

    def add_episode(self, ep, show_title=None, show_id=None, duration=0, label=None, link_show=True):
        """Epizóda → prehrateľná položka. link_show pridá do menu „Otvoriť reláciu“."""
        show_title = show_title or ep.get("name") or ""
        if label is None:
            label = "%s – %s" % (format_date(ep.get("date", "")), ep.get("subtitle") or ep.get("name") or show_title)
        li = xbmcgui.ListItem(label, offscreen=True)
        image = ep.get("image")
        _set_art(li, {"thumb": image, "icon": image, "landscape": image, "fanart": image or ku.ADDON_FANART})
        li.setProperty("IsPlayable", "true")

        plot = ep.get("plot") or ""
        if ep.get("available_until"):
            plot = (plot + "\n\n" if plot else "") + ku.tr(30027) % format_date(ep["available_until"])

        tag = li.getVideoInfoTag()
        tag.setMediaType("episode")
        tag.setTitle(ep.get("subtitle") or ep.get("name") or show_title)
        tag.setTvShowTitle(show_title)
        tag.setPlot(plot)
        if ep.get("date"):
            tag.setFirstAired(ep["date"])
            tag.setPremiered(ep["date"])
        if duration:
            tag.setDuration(int(duration))
        if ep.get("hd"):
            try:
                tag.addVideoStream(xbmc.VideoStreamDetail(width=1920, height=1080, codec="h264"))
            except (AttributeError, TypeError):
                pass

        context = self._watch_later_menu("episode", ep["id"], {
            "title": ep.get("subtitle") or ep.get("name"), "image": image, "plot": ep.get("plot"),
            "show_id": show_id, "show_title": show_title, "date": ep.get("date")})
        if show_id and link_show:
            context.append((ku.tr(30025), "Container.Update(%s)" % self.url(
                action="show", id=show_id, title=show_title)))
        li.addContextMenuItems(context)
        xbmcplugin.addDirectoryItem(self.handle, self.play_url(ep["id"]), li, isFolder=False)

    def add_live(self, channel, name, info=None):
        """Live kanál → prehrateľná položka s práve vysielaným programom (ak je známy)."""
        info = info or {}
        label = name
        if info.get("title"):
            label = "%s – %s" % (name, info["title"])
            if info.get("start") and info.get("stop"):
                label += " (%s–%s)" % (info["start"], info["stop"])
        li = xbmcgui.ListItem(label, offscreen=True)
        image = info.get("image")
        _set_art(li, {"thumb": image, "icon": image or ku.ADDON_ICON, "landscape": image,
                      "fanart": image or ku.ADDON_FANART})
        li.setProperty("IsPlayable", "true")
        tag = li.getVideoInfoTag()
        tag.setMediaType("video")
        tag.setTitle(label)
        if info.get("plot"):
            tag.setPlot(info["plot"])
        xbmcplugin.addDirectoryItem(self.handle, self.url(action="play_live", c=channel), li, isFolder=False)

    def add_action(self, label, url, icon="DefaultFolder.png", context=None):
        """Akčná položka (napr. nové hľadanie): nie priečinok ani video.

        Kodi ju po kliknutí spustí ako skript s handle -1, bez otvárania adresára.
        Akcia potom môže prejsť inam cez Container.Update; pri priečinku by to
        Kodi prebilo návratom späť, ak sa adresár ukončí ako neúspešný.
        """
        li = xbmcgui.ListItem(label, offscreen=True)
        _set_art(li, {"icon": icon, "thumb": icon, "fanart": ku.ADDON_FANART})
        li.setProperty("IsPlayable", "false")
        if context:
            li.addContextMenuItems(context)
        xbmcplugin.addDirectoryItem(self.handle, url, li, isFolder=False)

    def end(self, content="", cache_to_disc=True, update_listing=False):
        if content:
            xbmcplugin.setContent(self.handle, content)
        xbmcplugin.endOfDirectory(self.handle, succeeded=True,
                                  updateListing=update_listing, cacheToDisc=cache_to_disc)

    def fail(self):
        xbmcplugin.endOfDirectory(self.handle, succeeded=False)


def _kodi_major():
    try:
        return int(xbmc.getInfoLabel("System.BuildVersion").split(".")[0])
    except ValueError:
        return 21


def resolve(handle, path, info, use_isa=False, manifest="hls", subtitles=None):
    """Odovzdá Kodi čerstvú stream URL (setResolvedUrl)."""
    li = xbmcgui.ListItem(path=path, offscreen=True)
    _set_art(li, {"thumb": info.get("image")})
    tag = li.getVideoInfoTag()
    if info.get("title"):
        tag.setTitle(info["title"])
    if info.get("plot"):
        tag.setPlot(info["plot"])
    if info.get("duration"):
        tag.setDuration(int(info["duration"]))
    if use_isa:
        li.setProperty("inputstream", "inputstream.adaptive")
        if _kodi_major() < 21:  # od Kodi 21 ISA typ manifestu zistí sám
            li.setProperty("inputstream.adaptive.manifest_type", manifest)
        li.setMimeType("application/dash+xml" if manifest == "mpd" else "application/vnd.apple.mpegurl")
    else:
        li.setMimeType("application/vnd.apple.mpegurl")
    li.setContentLookup(False)
    if subtitles:
        li.setSubtitles(subtitles)
    xbmcplugin.setResolvedUrl(handle, True, li)
