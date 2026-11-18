# -*- coding: utf-8 -*-
"""HTTP klient a parsery neoficiálneho API archívu STVR.

Všetko, čo závisí od podoby webu stvr.sk, je v tomto súbore. Pri zmene webu
sa opravuje len tu. Modul nepoužíva žiadne xbmc* moduly, aby sa dal testovať
mimo Kodi (pozri tests/test_api.py a docs/API.md).
"""

import html
import json
import re
import socket
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

BASE_URL = "https://www.stvr.sk"
ARCHIVE_PATH = "/televizia/archiv"
CHUNK_PATH = "/chunk/tv-archiv"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; plugin.video.stvr; "
    "+https://github.com/tvadovic/plugin.video.stvr)"
)

# Hodnoty filtrov z HTML archívu (data-filter-value).
CHANNELS = [("1", "Jednotka"), ("2", "Dvojka"), ("3", ":24"), ("15", "Šport")]
LETTERS = [("9", "0-9")] + [(c, c.upper()) for c in "abcdefghijklmnopqrstuvwxyz"]
# Živé vysielanie: (c pre live5f.json, názov), poradie ako v menu stvr.sk/televizia.
LIVE_CHANNELS = [("1", "Jednotka"), ("2", "Dvojka"), ("3", ":24"), ("15", "Šport"),
                 ("4", "Live O"), ("6", "Live STVR"), ("5", "NR SR")]
FILTER_KEYS = ("ch", "l", "date", "content")

TTL_SECTION = 24 * 3600     # base-params a podžánre sa menia zriedka
TTL_DURATION = 30 * 24 * 3600


class ApiError(Exception):
    """Chyba komunikácie so STVR alebo neočakávaný formát odpovede."""


class GeoBlockedError(ApiError):
    """Server odmietol požiadavku (HTTP 403/451), typicky mimo SR."""


class NotAvailableError(ApiError):
    """Epizóda nemá dostupný stream (neexistuje, geoblokácia, licencia)."""


# ---------------------------------------------------------------- parsery ---

_RE_SERIES_ID = re.compile(r'data-series-id="(\d+)"')
_RE_HREF_IDS = re.compile(r'href="/televizia/archiv/(\d+)/(\d+)"')
_RE_ITEM_NAME = re.compile(r'data-item-name="([^"]*)"')
_RE_IMG = re.compile(r'<img[^>]*\ssrc="([^"]+)"')
_RE_GROUP_TITLE = re.compile(r'data-item-list-name="([^"]*)"')
_RE_MORE = re.compile(
    r'href="(/televizia/archiv/[^"?]+)(?:\?[^"]*)?"\s+data-item-name="Zobraziť viac"')
_RE_NAV = re.compile(
    r'<a\s+class="filter-carousel__slide[^"]*"[^>]*?href="(/televizia/archiv/[^"]+)"'
    r'[^>]*?data-datalayer-item="([^"]*)"')
_RE_BASE_PARAMS = re.compile(r'data-chunk-base-params="([^"]*)"')
_RE_NODE = re.compile(r'id="tv-archiv-results"[^>]*?data-archive-node="(\d+)"')
_RE_SCROLL = re.compile(r'<div data-infinite-scroll\s([^>]*)>')
_RE_ATTR = re.compile(r'data-([a-z-]+)="([^"]*)"')
_RE_ARCHIVE_URI = re.compile(r'/televizia/archiv/(\d+)/(\d+)')


def _text(value):
    """Odstráni HTML značky a entity, zjednoduší medzery."""
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", "", str(value))
    return re.sub(r"[ \t]+", " ", html.unescape(value)).strip()


def parse_show_items(fragment):
    """Vráti relácie z HTML (stránka žánru, chunk alebo jedna skupina).

    Každá relácia: {"id", "latest_episode", "title", "image"}.
    Duplicitné showId (rovnaká relácia vo viacerých skupinách) vynechá.
    """
    shows, seen = [], set()
    starts = [m.start() for m in _RE_SERIES_ID.finditer(fragment)] + [len(fragment)]
    for begin, end in zip(starts, starts[1:]):
        chunk = fragment[begin:end]
        show_id = _RE_SERIES_ID.match(chunk).group(1)
        href = _RE_HREF_IDS.search(chunk)
        name = _RE_ITEM_NAME.search(chunk)
        if not href or not name or show_id in seen:
            continue
        seen.add(show_id)
        img = _RE_IMG.search(chunk)
        shows.append({
            "id": show_id,
            "latest_episode": href.group(2),
            "title": _text(name.group(1)),
            "image": html.unescape(img.group(1)) if img else "",
        })
    return shows


def parse_paging(fragment):
    """Z kontajnera data-infinite-scroll vráti (rows_all, page, page_limit)."""
    m = _RE_SCROLL.search(fragment)
    if not m:
        return None, None, None
    attrs = dict(_RE_ATTR.findall(m.group(1)))

    def num(key):
        try:
            return int(attrs.get(key, ""))
        except ValueError:
            return None
    return num("rows-all"), num("page"), num("page-limit")


def parse_section(page_html, path):
    """Zo stránky /televizia/archiv/{path} vytiahne konfiguráciu chunku a podsekcie.

    Vracia {"base_params": "t=08&node=2806", "node": "2806", "children": [{"path", "title"}]}.
    Pre koreň (path == "") sú children žánre, pre žáner jeho podžánre.
    """
    base = _RE_BASE_PARAMS.search(page_html)
    node = _RE_NODE.search(page_html)
    prefix = ARCHIVE_PATH + "/" + (path + "/" if path else "")
    depth = prefix.count("/")
    children, seen = [], set()
    for href, title in _RE_NAV.findall(page_html):
        href = href.split("?")[0].rstrip("/")
        if not href.startswith(prefix) or href.count("/") != depth or href in seen:
            continue
        seen.add(href)
        children.append({"path": href[len(ARCHIVE_PATH) + 1:], "title": _text(title)})
    return {
        "base_params": html.unescape(base.group(1)) if base else "",
        "node": node.group(1) if node else "",
        "children": children,
    }


def parse_groups(fragment):
    """Koreň archívu s filtrom vráti relácie zoskupené podľa žánrov.

    Každá skupina: {"title", "path" (alebo None), "has_more", "shows"}.
    """
    parts = re.split(r'<div data-content-list="list"', fragment)[1:]
    groups = []
    for part in parts:
        title = _RE_GROUP_TITLE.search(part)
        if not title:
            continue
        more = _RE_MORE.search(part)
        groups.append({
            "title": _text(title.group(1)),
            "path": more.group(1)[len(ARCHIVE_PATH) + 1:] if more else None,
            "has_more": bool(more),
            "shows": parse_show_items(part),
        })
    return groups


def _air_date(air):
    return (air or "")[:10]


def parse_episodes(data):
    """JSON /json/tv/archiv → (zoznam epizód, celkový počet)."""
    if not isinstance(data, dict):
        raise ApiError("Neočakávaná odpoveď zoznamu epizód")
    episodes = []
    for item in data.get("program") or []:
        if not isinstance(item, dict) or not item.get("ID"):
            continue
        episodes.append({
            "id": str(item["ID"]),
            "name": _text(item.get("name")),
            "subtitle": _text(item.get("subtitle")),
            "air": item.get("air") or "",
            "date": _air_date(item.get("air")),
            "plot": _text(item.get("description")) or _text(item.get("synopsis")),
            "image": item.get("image") or "",
            "series": str(item.get("series") or ""),
            "hd": item.get("video_quality") == "HD",
            "cc": item.get("accessibility_cc") == "Y",
            "available_until": _air_date(item.get("license")),
        })
    try:
        total = int((data.get("paging") or {}).get("results"))
    except (TypeError, ValueError):
        total = None
    return episodes, total


def parse_length(value):
    """'00:29:21' → 1761 sekúnd; nesprávny formát → 0."""
    try:
        parts = [int(p) for p in str(value).split(":")]
    except ValueError:
        return 0
    seconds = 0
    for part in parts:
        seconds = seconds * 60 + part
    return seconds


def parse_stream(data):
    """JSON archive5f.json → slovník so streamom. Bez clipu vyhodí NotAvailableError."""
    clip = data.get("clip") if isinstance(data, dict) else None
    if not isinstance(clip, dict):
        raise NotAvailableError("Epizóda nemá clip")
    hls = dash = ""
    for source in clip.get("sources") or []:
        kind = (source.get("type") or "").lower()
        if "mpegurl" in kind and not hls:
            hls = source.get("src") or ""
        elif "dash" in kind and not dash:
            dash = source.get("src") or ""
    if not hls and not dash:
        raise NotAvailableError("Epizóda nemá zdroje videa")
    subtitles = []
    for track in ((clip.get("subtitles") or {}).get("tracks") or []):
        if track.get("src"):
            subtitles.append({"lang": track.get("lang") or "",
                              "label": track.get("label") or "",
                              "src": track["src"]})
    return {
        "hls": hls,
        "dash": dash,
        "subtitles": subtitles,
        "title": _text(clip.get("title")),
        "plot": _text(clip.get("description")),
        "image": clip.get("image") or "",
        "duration": parse_length(clip.get("length")),
    }


def parse_live(data):
    """JSON live5f.json → stream kanála a práve vysielaný program.

    Mimo vysielania (Live O, NR SR…) clip nemá program: chýba title
    a dateTimeStart == dateTimeStop.
    """
    info = parse_stream(data)
    clip = data["clip"]
    start, stop = clip.get("dateTimeStart") or "", clip.get("dateTimeStop") or ""
    has_program = bool(clip.get("title")) and start != stop
    info.update(
        title=(_text(clip.get("titleorig")) or info["title"]) if has_program else "",
        plot=info["plot"] if has_program else "",
        start=start[11:16] if has_program else "",
        stop=stop[11:16] if has_program else "",
        duration=0,
    )
    if "placeholder" in info["image"]:
        info["image"] = ""
    return info


_RE_LIVE_LOW = re.compile(r"-(?:mob|lq)(\.smil/)")


def live_full_quality(url):
    """Web dáva live HLS len do 480p (stv1-mob.smil, Šport stv4-lq.smil).

    Ten istý server s tým istým tokenom (nie je viazaný na cestu) má aj
    stv1.smil do 1080p. Ak URL nemá známu príponu, vráti ju nezmenenú.
    """
    return _RE_LIVE_LOW.sub(r"\1", url, count=1)


def parse_hls_master(text, base_url):
    """HLS master playlist → varianty zoradené od najvyššej kvality."""
    variants, pending = [], None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#EXT-X-STREAM-INF:"):
            res = re.search(r"RESOLUTION=\d+x(\d+)", line)
            bw = re.search(r"BANDWIDTH=(\d+)", line)
            pending = (int(res.group(1)) if res else 0, int(bw.group(1)) if bw else 0)
        elif line and not line.startswith("#") and pending:
            variants.append({"height": pending[0], "bandwidth": pending[1],
                             "url": urljoin(base_url, line)})
            pending = None
    variants.sort(key=lambda v: (v["height"], v["bandwidth"]), reverse=True)
    return variants


def pick_variant(variants, max_height):
    """Najlepší variant, ktorý nepresahuje max_height (inak najnižší)."""
    if not variants:
        return None
    fitting = [v for v in variants if v["height"] and v["height"] <= max_height]
    return fitting[0] if fitting else variants[-1]


def parse_search(data):
    """JSON /json/search/full (alebo lite) → (relácie s archívom, celkovo, ďalší offset)."""
    block = ((data or {}).get("blocks") or {}).get("video_series") or {}
    shows = []
    for hit in block.get("hits") or []:
        uri = hit.get("uri") or ""
        m = _RE_ARCHIVE_URI.search(uri) or _RE_ARCHIVE_URI.search(hit.get("latest_episode_uri") or "")
        if not m:
            continue  # relácia bez archívu (/televizia/program/…)
        shows.append({
            "id": m.group(1),
            "latest_episode": m.group(2),
            "title": _text(hit.get("name")),
            "plot": _text(hit.get("description")),
            "image": hit.get("thumbnail") or "",
        })
    try:
        total = int(block.get("total") or 0)
        more = int(block.get("more") or 0)
        offset = int(data.get("offset") or 0)
    except (TypeError, ValueError):
        total, more, offset = len(shows), 0, 0
    hits = len(block.get("hits") or [])
    next_offset = offset + hits if more > 0 and hits else None
    return shows, total, next_offset


def parse_calendar(data):
    """JSON kalendára → zoznam dátumov 'YYYY-MM-DD' (najnovšie prvé)."""
    days = ((data or {}).get("calendar") or {}).get("days") or {}
    if not isinstance(days, dict):
        return []
    return sorted((d[:10] for d, v in days.items() if v), reverse=True)


# ------------------------------------------------------------------ klient ---

class Client(object):
    """Prístup k archívu STVR. `cache` je objekt s metódami get(key, ttl) a set(key, value)."""

    def __init__(self, cache=None, list_ttl=1800, user_agent=DEFAULT_USER_AGENT, timeout=20):
        self.cache = cache
        self.list_ttl = list_ttl
        self.user_agent = user_agent
        self.timeout = timeout

    # --- HTTP

    def _url(self, path, params=None):
        url = path if path.startswith("http") else BASE_URL + path
        if params:
            url += ("&" if "?" in url else "?") + (
                params if isinstance(params, str) else urlencode(params))
        return url

    def fetch(self, path, params=None, ttl=0):
        """Stiahne text. ttl > 0 → použije cache (len pre zoznamy, nikdy pre stream)."""
        url = self._url(path, params)
        if ttl and self.cache is not None:
            hit = self.cache.get(url, ttl)
            if hit is not None:
                return hit
        request = Request(url, headers={"User-Agent": self.user_agent,
                                        "Accept-Language": "sk,en;q=0.5"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                text = response.read().decode(charset, "replace")
        except HTTPError as err:
            if err.code in (403, 451):
                raise GeoBlockedError("HTTP %d: %s" % (err.code, url))
            raise ApiError("HTTP %d: %s" % (err.code, url))
        except (URLError, socket.timeout, OSError) as err:
            raise ApiError("Sieťová chyba: %s (%s)" % (err, url))
        if ttl and self.cache is not None:
            self.cache.set(url, text)
        return text

    def fetch_json(self, path, params=None, ttl=0):
        text = self.fetch(path, params, ttl)
        try:
            return json.loads(text)
        except ValueError:
            raise ApiError("Neplatný JSON z %s" % path)

    # --- relácie

    def section(self, path=""):
        """Konfigurácia sekcie archívu: base_params, node, children (žánre/podžánre)."""
        page = self.fetch(ARCHIVE_PATH + ("/" + path if path else ""), ttl=TTL_SECTION)
        info = parse_section(page, path)
        if not info["base_params"]:
            raise ApiError("Stránka %s nemá konfiguráciu zoznamu" % (path or "archívu"))
        return info

    def genres(self):
        return self.section("")["children"]

    def shows(self, path, filters=None, page=1):
        """Relácie žánru/podžánru (s voliteľnými filtrami). Vracia (relácie, má_ďalšiu)."""
        params = self.section(path)["base_params"]
        extra = [(k, v) for k, v in (filters or {}).items() if k in FILTER_KEYS and v]
        extra.append(("page", str(page)))
        fragment = self.fetch(CHUNK_PATH, params + "&" + urlencode(extra), ttl=self.list_ttl)
        shows = parse_show_items(fragment)
        total, _, limit = parse_paging(fragment)
        if total is not None and limit:
            has_more = page * limit < total
        else:
            has_more = bool(shows) and len(shows) >= (limit or 20)
        return shows, has_more

    def filtered_groups(self, filters):
        """Koreň archívu s filtrom (písmeno, kanál, dátum…) → skupiny po žánroch."""
        params = self.section("")["base_params"]
        extra = [(k, v) for k, v in filters.items() if k in FILTER_KEYS and v]
        fragment = self.fetch(CHUNK_PATH, params + "&" + urlencode(extra), ttl=self.list_ttl)
        groups = parse_groups(fragment)
        by_title = dict((g["title"], g["path"]) for g in self.genres())
        for group in groups:
            if not group["path"]:
                group["path"] = by_title.get(group["title"])
        return groups

    def calendar(self, month):
        """Dni mesiaca ('YYYY-MM'), v ktorých je v archíve niečo vysielané."""
        node = self.section("")["node"]
        params = {"calendar": "Y", "d": month}
        if node:
            params["node"] = node
        return parse_calendar(self.fetch_json("/json/tv/archiv", params, ttl=self.list_ttl))

    # --- epizódy

    def episodes(self, show_id, page=1, per_page=30):
        """Epizódy relácie (všetky série), najnovšie prvé. Vracia (epizódy, má_ďalšiu)."""
        params = {"e": "1", "archive": "1", "s": show_id,
                  "p": str(page), "l": str(per_page), "o": "desc"}
        episodes, total = parse_episodes(
            self.fetch_json("/json/tv/archiv", params, ttl=self.list_ttl))
        if total is not None:
            has_more = page * per_page < total
        else:
            has_more = len(episodes) >= per_page
        return episodes, has_more

    def day_episodes(self, date):
        """Všetky epizódy vysielané v deň 'YYYY-MM-DD', chronologicky."""
        params = {"e": "1", "archive": "1", "d": date, "p": "1", "l": "500", "o": "asc"}
        return parse_episodes(self.fetch_json("/json/tv/archiv", params, ttl=self.list_ttl))[0]

    def stream(self, episode_id):
        """Čerstvý stream epizódy. Nikdy sa nekešuje (token platí ~2 h, možno viazaný na IP)."""
        data = self.fetch_json("/json/archive5f.json", {"id": episode_id})
        info = parse_stream(data)
        if self.cache is not None and info["duration"]:
            self.cache.set("duration:%s" % episode_id, info["duration"])
        return info

    def duration(self, episode_id):
        """Dĺžka epizódy v sekundách. Kešuje sa len číslo, nie odpoveď s tokenom."""
        key = "duration:%s" % episode_id
        if self.cache is not None:
            hit = self.cache.get(key, TTL_DURATION)
            if hit is not None:
                return hit
        try:
            seconds = parse_stream(self.fetch_json("/json/archive5f.json", {"id": episode_id}))["duration"]
        except ApiError:
            seconds = 0
        if self.cache is not None:
            self.cache.set(key, seconds)
        return seconds

    def durations(self, episode_ids, workers=6):
        """Dĺžky viacerých epizód naraz (paralelne). Vracia {id: sekundy}."""
        ids = list(episode_ids)
        if not ids:
            return {}
        with ThreadPoolExecutor(max_workers=min(workers, len(ids))) as pool:
            return dict(zip(ids, pool.map(self.duration, ids)))

    # --- živé vysielanie

    def live(self, channel):
        """Čerstvý live stream kanála a aktuálny program. Nekešuje sa (token)."""
        return parse_live(self.fetch_json("/json/live5f.json", {"c": channel}))

    def live_all(self, channels, workers=7):
        """Aktuálny program viacerých kanálov naraz. Kanál s chybou má None."""
        channels = list(channels)

        def one(channel):
            try:
                return self.live(channel)
            except ApiError:
                return None
        if not channels:
            return {}
        with ThreadPoolExecutor(max_workers=min(workers, len(channels))) as pool:
            return dict(zip(channels, pool.map(one, channels)))

    def hls_variants(self, master_url):
        return parse_hls_master(self.fetch(master_url), master_url)

    # --- vyhľadávanie

    def search(self, query, offset=0):
        """Vyhľadá TV relácie s archívom. Vracia (relácie, celkovo, ďalší offset alebo None)."""
        params = {"q": query, "s": "video_series"}
        if offset:
            params["o"] = str(offset)
        return parse_search(self.fetch_json("/json/search/full", params, ttl=self.list_ttl))
