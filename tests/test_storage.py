# -*- coding: utf-8 -*-
from resources.lib import storage


def test_cache_ttl(tmp_path):
    cache = storage.Cache(str(tmp_path / "cache"))
    assert cache.get("k", 60) is None
    cache.set("k", {"a": "č"})
    assert cache.get("k", 60) == {"a": "č"}
    assert cache.get("k", -1) is None
    cache.clear()
    assert cache.get("k", 60) is None


def test_watch_later(tmp_path):
    wl = storage.WatchLater(str(tmp_path / "wl.json"))
    assert wl.items() == []
    wl.add("show", 14126, title="Duel", image="i.jpg")
    wl.add("episode", "630571", title="Duel", show_id="14126", date="2026-11-16", unknown="x")
    assert [i["kind"] for i in wl.items()] == ["episode", "show"]
    assert wl.contains("show", "14126") and not wl.contains("episode", "14126")
    assert "unknown" not in wl.items()[0]
    wl.add("show", "14126", title="Duel 2")  # znovu pridané ide navrch, bez duplicity
    assert len(wl.items()) == 2 and wl.items()[0]["title"] == "Duel 2"
    assert wl.remove("show", "14126") and not wl.remove("show", "14126")
    assert len(wl.items()) == 1


def test_watch_later_corrupted_file(tmp_path):
    path = tmp_path / "wl.json"
    path.write_text("{nie je json", encoding="utf-8")
    assert storage.WatchLater(str(path)).items() == []


def test_search_history(tmp_path):
    history = storage.SearchHistory(str(tmp_path / "h.json"), limit=3)
    for query in ("duel", "správy", "Duel", "  ", "hokej", "film"):
        history.add(query)
    assert history.items() == ["film", "hokej", "Duel"]
    history.remove("hokej")
    assert history.items() == ["film", "Duel"]
    history.clear()
    assert history.items() == []
