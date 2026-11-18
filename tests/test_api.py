# -*- coding: utf-8 -*-
"""Testy parserov api.py nad uloženými odpoveďami v tests/fixtures/."""

import json
import os

import pytest

from resources.lib import api

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read()


def fixture_json(name):
    return json.loads(fixture(name))


# --- zoznamy relácií

def test_show_items_from_genre_page():
    shows = api.parse_show_items(fixture("genre_zabava.html"))
    assert len(shows) == 20
    first = shows[0]
    assert first["id"].isdigit() and first["latest_episode"].isdigit()
    assert first["title"]
    assert first["image"].startswith("https://")


def test_show_items_from_chunk_page():
    shows = api.parse_show_items(fixture("chunk_zabava_page2.html"))
    assert len(shows) == 20
    assert shows[0] == {
        "id": "21943",
        "latest_episode": "588773",
        "title": "Cena regiónov",
        "image": "https://www.stvr.sk/media/a501/image/file/2/1507/cenaregionov-1920x1080.jpg",
    }


def test_paging():
    assert api.parse_paging(fixture("chunk_zabava_page2.html")) == (121, 2, 20)
    assert api.parse_paging(fixture("genre_zabava.html")) == (121, 1, 20)
    assert api.parse_paging("<div>nič</div>") == (None, None, None)


def test_section_root_lists_genres():
    info = api.parse_section(fixture("archive_root.html"), "")
    assert info["base_params"] == "charindex=001:008&path_url=televizia/archiv"
    assert info["node"] == "276"
    paths = [c["path"] for c in info["children"]]
    assert paths[:3] == ["filmy", "serialy", "zabava"]
    assert "umenie" in paths
    assert {"path": "sport", "title": "Šport"} in info["children"]


def test_section_genre_lists_subgenres():
    info = api.parse_section(fixture("genre_zabava.html"), "zabava")
    assert info["base_params"] == "t=08&node=2806"
    assert {"path": "zabava/varenie", "title": "Varenie"} in info["children"]
    assert all(c["path"].startswith("zabava/") for c in info["children"])


def test_groups_from_filtered_root():
    groups = api.parse_groups(fixture("chunk_root_letter_a.html"))
    titles = [g["title"] for g in groups]
    assert titles[0] == "Filmy"
    assert all(g["shows"] for g in groups)
    publicistika = [g for g in groups if g["title"] == "Publicistika"][0]
    assert publicistika["has_more"] and publicistika["path"] == "publicistika"
    # "Zobraziť viac" nie je relácia
    assert all(s["title"] != "Zobraziť viac" for g in groups for s in g["shows"])


def test_groups_from_date_filter():
    groups = api.parse_groups(fixture("chunk_root_date.html"))
    assert groups and all(g["title"] for g in groups)


# --- epizódy

def test_episodes_month():
    episodes, total = api.parse_episodes(fixture_json("episodes_month.json"))
    assert total == 12 and len(episodes) == 12
    ep = episodes[0]
    assert ep["id"] == "630608"
    assert ep["date"] == "2026-11-17"
    assert ep["plot"] == "Vedomostná súťaž s jedným moderátorom a dvoma hráčmi."
    assert ep["cc"] is True and ep["hd"] is True
    assert ep["series"] == "22948"


def test_episodes_paged_total():
    episodes, total = api.parse_episodes(fixture_json("episodes_all_page.json"))
    assert total == 2173 and len(episodes) == 5


def test_episodes_invalid():
    with pytest.raises(api.ApiError):
        api.parse_episodes([])


# --- stream

def test_stream():
    info = api.parse_stream(fixture_json("archive5f.json"))
    assert info["hls"].endswith("playlist.m3u8?auth=<TOKEN>")
    assert info["dash"].endswith("manifest.mpd?auth=<TOKEN>")
    assert info["duration"] == 29 * 60 + 21
    assert info["subtitles"][0]["lang"] == "sk"
    assert info["subtitles"][0]["src"].startswith("https://www.stvr.sk/plain/webvtt/")


def test_stream_missing_clip():
    with pytest.raises(api.NotAvailableError):
        api.parse_stream(fixture_json("archive5f_missing.json"))


def test_stream_without_sources():
    with pytest.raises(api.NotAvailableError):
        api.parse_stream({"clip": {"title": "x", "sources": []}})


@pytest.mark.parametrize("value,seconds", [
    ("00:29:21", 1761), ("01:00:00", 3600), ("45:10", 2710), ("", 0), (None, 0), ("x", 0)])
def test_parse_length(value, seconds):
    assert api.parse_length(value) == seconds


def test_hls_master_and_pick():
    variants = api.parse_hls_master(fixture("master.m3u8"), "https://n11.stv.livebox.sk/x/playlist.m3u8")
    assert [v["height"] for v in variants] == [1080, 720, 480, 360]
    assert variants[0]["url"].startswith("https://n11.stv.livebox.sk/vod/")
    assert api.pick_variant(variants, 720)["height"] == 720
    assert api.pick_variant(variants, 600)["height"] == 480
    assert api.pick_variant(variants, 100)["height"] == 360
    assert api.pick_variant([], 720) is None


def test_hls_master_relative_urls():
    text = "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1,RESOLUTION=640x360\nlow/index.m3u8\n"
    variants = api.parse_hls_master(text, "https://h/a/b/playlist.m3u8")
    assert variants[0]["url"] == "https://h/a/b/low/index.m3u8"


# --- vyhľadávanie a kalendár

def test_search_full_skips_shows_without_archive():
    data = fixture_json("search_full.json")
    shows, total, next_offset = api.parse_search(data)
    hits = data["blocks"]["video_series"]["hits"]
    assert len(shows) < len(hits)  # /televizia/program/… bez archívu sú vynechané
    assert all(s["id"].isdigit() for s in shows)
    assert total == 210 and next_offset == 40


def test_search_lite():
    shows, total, next_offset = api.parse_search(fixture_json("search_lite.json"))
    assert [s["title"] for s in shows] == ["Duel", "Duel šampiónov", "Duel junior"]
    assert shows[0]["id"] == "14126"
    assert next_offset is None


def test_search_lite_multiple_blocks():
    shows, _, _ = api.parse_search(fixture_json("search_lite_multi.json"))
    assert shows  # berie len blok video_series, ostatné ignoruje


def test_calendar():
    days = api.parse_calendar(fixture_json("calendar.json"))
    assert days[0] == "2026-11-18" and days[-1] == "2026-11-01"
    assert api.parse_calendar({}) == []


def test_episodes_of_day():
    episodes, total = api.parse_episodes(fixture_json("episodes_day.json"))
    assert total == 48 and len(episodes) == 6
    assert [e["air"] for e in episodes] == sorted(e["air"] for e in episodes)
    assert all(e["date"] == "2026-11-17" for e in episodes)
