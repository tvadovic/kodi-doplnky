# -*- coding: utf-8 -*-
"""Router (main.py) so stubmi xbmc* a odpoveďami z fixtures – bez siete."""
import os
import re
from urllib.parse import parse_qsl

import pytest

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from resources.lib import api

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
BASE = "plugin://plugin.video.stvr/"

ROUTES = [
    (r"/televizia/archiv$", "archive_root.html"),
    (r"/televizia/archiv/zabava$", "genre_zabava.html"),
    (r"chunk/tv-archiv\?charindex=.*&l=", "chunk_root_letter_a.html"),
    (r"chunk/tv-archiv\?t=08&node=2806&page=1$", "genre_zabava.html"),
    (r"chunk/tv-archiv\?t=08&node=2806&page=2$", "chunk_zabava_page2.html"),
    (r"chunk/tv-archiv\?t=08&node=2806&l=d", "chunk_zabava_letter_d.html"),
    (r"calendar=Y", "calendar.json"),
    (r"json/tv/archiv\?.*&s=", "episodes_all_page.json"),
    (r"json/tv/archiv\?.*&d=\d{4}-\d\d-\d\d", "episodes_day.json"),
    (r"archive5f\.json\?id=630571", "archive5f.json"),
    (r"archive5f\.json", "archive5f_missing.json"),
    (r"search/full", "search_full.json"),
    (r"live5f\.json\?c=1$", "live5f.json"),
    (r"live5f\.json\?c=99$", "archive5f_missing.json"),
    (r"live5f\.json\?c=2$", "live5f_norights.json"),
    (r"live5f\.json", "live5f_offline.json"),
    (r"stv-tv/_definst_/stv\d\.smil/playlist\.m3u8", "live_master.m3u8"),
    (r"playlist\.m3u8", "master.m3u8"),
]


def _fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read()


def fake_fetch(self, path, params=None, ttl=0):
    url = self._url(path, params)
    for pattern, name in ROUTES:
        if re.search(pattern, url):
            return _fixture(name)
    if ".vtt" in url:
        return "WEBVTT\n"
    raise api.ApiError("Neočakávaná URL v teste: " + url)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(api.Client, "fetch", fake_fetch)
    xbmcplugin.reset()
    del xbmcgui.NOTIFICATIONS[:], xbmcgui.DIALOGS[:], xbmc.BUILTINS[:]
    xbmcaddon.SETTINGS.clear()
    xbmcaddon.SETTINGS["fetch_duration"] = "false"
    yield


def run(query):
    import main
    xbmcplugin.reset()
    main.Router([BASE, "1", "?" + query]).run()
    return [(li.getLabel(), url, folder) for url, li, folder in xbmcplugin.ITEMS]


def test_root_menu():
    items = run("")
    assert [i[0] for i in items][:4] == ["Naživo", "Žánre", "A–Z", "Kanály"]
    assert all(folder for _, _, folder in items)
    assert xbmcplugin.STATE["cache_to_disc"] is False   # nové položky menu hneď po aktualizácii


def test_genres_and_genre_listing():
    assert ("Zábava", BASE + "?action=genre&path=zabava", True) in run("action=genres")
    items = run("action=genre&path=zabava")
    assert items[0][0] == "Podžánre…"
    assert len(items) == 22  # podžánre + 20 relácií + ďalšia strana
    assert items[-1][1] == BASE + "?action=shows&path=zabava&page=2"
    assert xbmcplugin.STATE["content"] == "tvshows"


def test_paging_and_filtered_genre():
    items = run("action=shows&path=zabava&page=2")
    assert len(items) == 21 and items[-1][0] == "Ďalšia strana…"  # 2 × 20 < 121
    items = run("action=shows&path=zabava&l=d")
    assert len(items) == 6 and all("page=" not in i[1] for i in items)


def test_filter_lists_genres_with_filter():
    items = run("action=filter&l=a")
    assert items[0][0] == "Filmy"
    assert all(i[1].endswith("&l=a") for i in items)


def test_show_episodes_have_stable_play_urls():
    items = run("action=show&id=14126&title=Duel")
    assert items[0][1] == BASE + "?action=play&id=629324"
    li = xbmcplugin.ITEMS[0][1]
    assert li.getProperty("IsPlayable") == "true"
    assert li.getVideoInfoTag().info["tvshowtitle"] == "Duel"
    assert not any(label == "Otvoriť reláciu" for label, _ in li.context)
    assert items[-1][0] == "Staršie…" and "page=2" in items[-1][1]


def test_calendar_and_day():
    items = run("action=calendar&month=2026-11")
    assert items[0][0] == "St 18.11.2026"
    assert items[-1][1].endswith("action=calendar&month=2026-10")
    items = run("action=day&date=2026-11-17")
    assert items[0][0].startswith("06:05  ")
    assert any(label == "Otvoriť reláciu" for label, _ in xbmcplugin.ITEMS[0][1].context)


def test_new_search_is_action_item_not_folder():
    # Priečinok, ktorý skončí succeeded=False, Kodi vráti späť a prebije Container.Update.
    items = run("action=search")
    assert items[0][0] == "Nové hľadanie…" and items[0][2] is False
    assert xbmcplugin.ITEMS[0][1].getProperty("IsPlayable") == "false"


def test_search_new_opens_results():
    xbmc.KEYBOARD_INPUT[:] = ["duel"]
    run("action=search_new")
    assert xbmc.BUILTINS == ["Container.Update(%s?action=search_results&q=duel)" % BASE]
    assert "succeeded" not in xbmcplugin.STATE  # akcia neukončuje žiadny adresár
    assert [i[0] for i in run("action=search")][1] == "duel"


def test_search_new_cancelled():
    xbmc.KEYBOARD_INPUT[:] = []
    run("action=search_new")
    assert xbmc.BUILTINS == [] and "succeeded" not in xbmcplugin.STATE


def test_search_too_short():
    xbmc.KEYBOARD_INPUT[:] = ["du"]
    run("action=search_new")
    assert xbmcgui.NOTIFICATIONS == ["Zadajte aspoň 3 znaky"]
    assert xbmc.BUILTINS == []


def test_search_results_paging():
    items = run("action=search_results&q=slovensko")
    assert items[-1][1].endswith("offset=40")


def test_play_resolves_fresh_hls_with_subtitles():
    run("action=play&id=630571")
    ok, li = xbmcplugin.STATE["resolved"]
    assert ok and li.getPath().endswith("playlist.m3u8?auth=<TOKEN>")
    assert li.mimetype == "application/vnd.apple.mpegurl"
    assert li.subtitles and li.subtitles[0].endswith("630571.sk.vtt")
    assert "inputstream" not in li.properties


def test_play_max_quality_picks_variant():
    xbmcaddon.SETTINGS["max_quality"] = "2"  # 720p
    run("action=play&id=630571")
    assert "00185390-2.mp4" in xbmcplugin.STATE["resolved"][1].getPath()


def test_play_with_inputstream_adaptive_dash():
    xbmcaddon.SETTINGS.update(use_isa="true", isa_manifest="1")
    xbmc.INSTALLED_ADDONS.add("inputstream.adaptive")
    try:
        run("action=play&id=630571")
    finally:
        xbmc.INSTALLED_ADDONS.clear()
    li = xbmcplugin.STATE["resolved"][1]
    assert li.properties["inputstream"] == "inputstream.adaptive"
    assert li.getPath().endswith("manifest.mpd?auth=<TOKEN>")


def test_play_isa_setting_ignored_when_not_installed():
    xbmcaddon.SETTINGS.update(use_isa="true", isa_manifest="1")
    run("action=play&id=630571")
    assert "inputstream" not in xbmcplugin.STATE["resolved"][1].properties


def test_live_lists_seven_channels_with_program():
    items = run("action=live")
    assert len(items) == 7
    assert items[0] == ("Jednotka – Dámsky klub (12:25–13:55)", BASE + "?action=play_live&c=1", False)
    assert items[-1] == ("NR SR", BASE + "?action=play_live&c=5", False)   # mimo vysielania
    assert xbmcplugin.ITEMS[0][1].getProperty("IsPlayable") == "true"
    assert items[1][0] == "[COLOR grey]Dvojka – Vedeli ste? (16:00–16:25) – nevysiela sa online[/COLOR]"
    assert xbmcplugin.ITEMS[1][1].tag.info["plot"].startswith("STVR nemá na tento program práva")


def test_play_live_without_rights_still_plays_and_notifies():
    run("action=play_live&c=2")
    assert xbmcplugin.STATE["resolved"][0] is True
    assert xbmcgui.NOTIFICATIONS == ["Vedeli ste? – nevysiela sa online"]


def test_play_live_with_rights_does_not_notify():
    run("action=play_live&c=1")
    assert xbmcgui.NOTIFICATIONS == []


def test_live_list_survives_failing_channel(monkeypatch):
    def flaky(self, path, params=None, ttl=0):
        if "c=2" in self._url(path, params):
            raise api.ApiError("timeout")
        return fake_fetch(self, path, params, ttl)
    monkeypatch.setattr(api.Client, "fetch", flaky)
    labels = [i[0] for i in run("action=live")]
    assert len(labels) == 7 and labels[1] == "Dvojka"


def test_play_live_prefers_full_quality_master():
    run("action=play_live&c=1")
    ok, li = xbmcplugin.STATE["resolved"]
    assert ok and li.getPath().endswith("/stv1.smil/playlist.m3u8?auth=<TOKEN>")
    assert li.mimetype == "application/vnd.apple.mpegurl"


def test_play_live_max_quality_picks_variant():
    xbmcaddon.SETTINGS["max_quality"] = "2"  # 720p
    run("action=play_live&c=1")
    assert xbmcplugin.STATE["resolved"][1].getPath().endswith("SK-stv1.smil/chunklist_b2691072.m3u8")


def test_play_live_falls_back_to_official_master(monkeypatch):
    def no_full(self, path, params=None, ttl=0):
        if "/stv1.smil/" in self._url(path, params):
            raise api.ApiError("HTTP 404")
        return fake_fetch(self, path, params, ttl)
    monkeypatch.setattr(api.Client, "fetch", no_full)
    run("action=play_live&c=1")
    assert xbmcplugin.STATE["resolved"][1].getPath().endswith("stv1-mob.smil/playlist.m3u8?auth=<TOKEN>")


def test_play_live_unavailable():
    run("action=play_live&c=99")
    assert xbmcplugin.STATE["resolved"][0] is False
    assert "nie je dostupné" in xbmcgui.DIALOGS[0]


def test_play_unavailable_shows_dialog():
    run("action=play&id=1")
    assert xbmcplugin.STATE["resolved"][0] is False
    assert "nie je dostupné" in xbmcgui.DIALOGS[0]


def test_network_error_notifies_and_fails(monkeypatch):
    def broken(self, path, params=None, ttl=0):
        raise api.ApiError("offline")
    monkeypatch.setattr(api.Client, "fetch", broken)
    run("action=genres")
    assert xbmcplugin.STATE["succeeded"] is False
    assert xbmcgui.NOTIFICATIONS == ["Nepodarilo sa načítať údaje zo STVR"]


def test_geoblock_shows_dialog(monkeypatch):
    def blocked(self, path, params=None, ttl=0):
        raise api.GeoBlockedError("HTTP 403")
    monkeypatch.setattr(api.Client, "fetch", blocked)
    run("action=show&id=1")
    assert "len zo Slovenska" in xbmcgui.DIALOGS[0]


def test_watch_later_roundtrip():
    run("action=show&id=14126&title=Duel")
    add = [cmd for label, cmd in xbmcplugin.ITEMS[0][1].context if label == "Pridať do Pozrieť neskôr"][0]
    query = add[len("RunPlugin(%s?" % BASE):-1]
    run(query)
    assert xbmcgui.NOTIFICATIONS[-1] == "Pridané do Pozrieť neskôr"
    items = run("action=watchlater")
    assert items[0][1] == BASE + "?action=play&id=629324"
    assert items[0][0].startswith("Duel – ")
    episode_id = dict(parse_qsl(query))["id"]
    run("action=wl_remove&kind=episode&id=" + episode_id)
    assert run("action=watchlater") == []


def test_unknown_action_fails_cleanly():
    run("action=nonsense")
    assert xbmcplugin.STATE["succeeded"] is False
