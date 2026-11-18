# -*- coding: utf-8 -*-
"""Live smoke test proti skutočnému API STVR.

Predvolene sa preskakuje. Spustenie (zo slovenskej IP):
    STVR_LIVE=1 python -m pytest tests/test_live.py -v
Overuje, že web stále vyzerá tak, ako očakávajú parsery v api.py.
"""

import os
from urllib.request import Request, urlopen

import pytest

from resources.lib import api

pytestmark = pytest.mark.skipif(not os.environ.get("STVR_LIVE"), reason="nastav STVR_LIVE=1")


@pytest.fixture(scope="module")
def client():
    return api.Client(cache=None, user_agent=api.DEFAULT_USER_AGENT)


def test_genres(client):
    paths = [g["path"] for g in client.genres()]
    assert {"filmy", "serialy", "zabava", "sport"} <= set(paths)


def test_genre_paging(client):
    shows, has_more = client.shows("zabava", page=1)
    assert len(shows) == 20 and has_more
    page2, _ = client.shows("zabava", page=2)
    assert page2 and not {s["id"] for s in shows} & {s["id"] for s in page2}


def test_subgenres(client):
    children = client.section("zabava")["children"]
    assert children
    shows, _ = client.shows(children[0]["path"])
    assert shows


def test_filters(client):
    for filters in ({"l": "d"}, {"ch": "1"}, {"content": "kids"}):
        groups = client.filtered_groups(filters)
        assert groups and all(g["path"] for g in groups), filters


def test_episodes_and_stream(client):
    shows, _ = client.shows("zabava")
    episodes, _ = client.episodes(shows[0]["id"], per_page=5)
    assert episodes
    info = client.stream(episodes[0]["id"])
    assert info["hls"] and "auth=" in info["hls"]
    variants = client.hls_variants(info["hls"])
    assert variants and variants[0]["height"] >= 720
    # chunklist variantu sa dá stiahnuť (bez Referer, bez cookies)
    with urlopen(Request(variants[-1]["url"], headers={"User-Agent": api.DEFAULT_USER_AGENT}), timeout=20) as r:
        assert r.read(7) == b"#EXTM3U"


def test_calendar_and_day(client):
    days = client.calendar(__import__("datetime").date.today().strftime("%Y-%m"))
    assert days
    assert client.day_episodes(days[-1])


def test_search(client):
    shows, total, _ = client.search("duel")
    assert any(s["title"] == "Duel" for s in shows)
