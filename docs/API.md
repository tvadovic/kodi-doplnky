# Neoficiálne API archívu STVR

Zistené z webu `https://www.stvr.sk/televizia/archiv` a z `/media/new/js/complete.min.js`
(objekty `STVRArchiveFilter`, `STVRArchiveCalendar`, trieda `FullSearch`).
Overené 18. 11. 2026 zo slovenskej IP. Nič z toho nie je oficiálne zdokumentované,
preto je všetko parsovanie v doplnku v jednom súbore: `resources/lib/api.py`.

Ukážkové odpovede sú v `tests/fixtures/` (auth tokeny sú nahradené `<TOKEN>`,
IP klienta `0.0.0.0`).

Žiadny endpoint nevyžaduje cookies, prihlásenie ani `Referer`.

---

## 1. Zoznam relácií (HTML)

### Stránky
| URL | Obsah |
|---|---|
| `/televizia/archiv` | „Odporúčame“ + ukážky po žánroch (5 na žáner) |
| `/televizia/archiv/{žáner}` | relácie žánru, 20 na stránku |
| `/televizia/archiv/{žáner}/{podžáner}` | relácie podžánru |

Položka relácie (rovnaká na stránke aj v chunku):

```html
<div class=" tv-archiv__item" data-list-item data-series-id="21943">
  <a href="/televizia/archiv/21943/588773" data-item-name="Cena regiónov">
    <picture>
      <source srcset="…/cenaregionov-1920x1080.webp" type="image/webp" />
      <img src="…/cenaregionov-1920x1080.jpg" alt="Cena regiónov" … />
    </picture>
    <h2 …>Cena regiónov</h2>      <!-- na koreni archívu je to <h3> -->
  </a>
</div>
```

* `data-series-id` = **showId** (rovnaké ako prvé číslo v `href`).
* druhé číslo v `href` = najnovšia epizóda.
* Na koreni má 5. položka v skupine triedu `d-none d-xl-block` (len desktop); pre nás nehrá rolu.

Žánre a podžánre sú odkazy `<a class="filter-carousel__slide …" href="/televizia/archiv/…" data-datalayer-item="Názov">`.
Na koreni sú to žánre, na stránke žánru jeho podžánre.

### Parametre chunku a stránkovanie („nekonečné scrollovanie“)

Kontajner výsledkov nesie konfiguráciu:

```html
<div id="tv-archiv-results"
     data-filter-params="ch,l,date,content,acc"
     data-filter-params-multi="content,acc"
     data-filter-active="l=d"
     data-archive-node="276"
     data-chunk-url="/chunk/tv-archiv"
     data-chunk-base-params="t=08&amp;node=2806">
  <div data-infinite-scroll data-rows-all="121" data-page="1" data-page-limit="20"> … </div>
```

Ďalšie stránky: **`GET /chunk/tv-archiv?{base-params}&{filtre}&page={N}`**.
Web posiela aj `after={posledné seriesId}`, ale server ho ignoruje a stačí `page`.
`page=1` tiež funguje, takže chunk sa dá použiť aj na prvú stránku.
Odpoveď je HTML fragment s rovnakými položkami a `data-infinite-scroll` (`data-rows-all` = celkový počet).
Za poslednou stránkou príde 0 položiek.

Base-params (stav 11/2026):

| žáner | slug | base-params | relácií |
|---|---|---|---|
| Filmy | `filmy` | `t=f&node=2800` | 15 |
| Seriály | `serialy` | `t=s&node=2801` | 56 |
| Zábava | `zabava` | `t=08&node=2806` | 121 |
| Spravodajstvo | `spravodajstvo` | `t=06&node=2802` | 67 |
| Publicistika | `publicistika` | `t=05&node=2803` | 235 |
| Šport | `sport` | `t=07&node=2804` | 55 |
| Dokument | `dokument` | `t=01&node=2809` | 320 |
| Hudba | `hudba` | `t=03&node=2808` | 143 |
| Vzdelávanie | `vzdelavanie` | `t=09&node=2805` | 38 |
| Náboženstvo | `nabozenstvo` | `t=04&node=2807` | 9 |
| Umenie | `umenie` | `t=&node=2810&sub=0205,0217,0220,0239` | 29 |
| koreň | – | `charindex=001:008&path_url=televizia/archiv` | – |

Podžánre majú vlastný `node` a `sub`, napr. `zabava/varenie` → `t=08&node=2870&sub=0814`.
Doplnok ich nemá natvrdo: base-params číta zo stránky (`data-chunk-base-params`), kešované 24 h.

### Filtre (query parametre; fungujú na stránke aj v chunku)

| Filter na webe | parameter | hodnoty |
|---|---|---|
| Kanál | `ch` | `1` Jednotka, `2` Dvojka, `3` :24, `15` Šport |
| Abeceda | `l` | `9` (= 0-9), `a`…`z` |
| Pre deti | `content` | `kids` |
| Európska tvorba | `content` | `eu` (viac hodnôt cez čiarku: `kids,eu`) |
| Kalendár | `date` | `YYYY-MM-DD` = relácie vysielané v daný deň |
| (prístupnosť) | `acc` | multi, hodnoty nezistené (v UI sa momentálne nezobrazuje) |

**Na koreni** (`charindex=001:008&path_url=televizia/archiv`) filter nevráti plochý zoznam,
ale skupiny po žánroch (`<h2 data-item-list-name="Šport">`), max. 5 položiek na skupinu
a odkaz `<a … data-item-name="Zobraziť viac" href="/televizia/archiv/sport?ch=3">`, ak je ich viac.
Bez base-params (`/chunk/tv-archiv?l=a`) server vráti prázdnu odpoveď.

Doplnok preto pri A–Z, kanáloch, „Pre deti“, „Európska tvorba“ a kalendári najprv
zavolá koreň s filtrom (zistí, v ktorých žánroch niečo je) a potom ponúkne žánre,
ktoré sa otvoria ako `chunk?{base žánru}&{filter}&page=N`.

### Kalendár
Pozri aj epizódy podľa dňa v časti 2.

`GET /json/tv/archiv?calendar=Y&d={YYYY-MM}[&t=…][&node=…][&ch=…&letter=…&content=…]`

```json
{"paging":{"page":"1","size":"0","results":"18"},
 "calendar":{"year":"2026","month":"11","days":{"2026-11-01":1, "…":1}}}
```
Dni, v ktorých je v archíve niečo vysielané. Pozor: tu sa písmeno volá `letter`, nie `l`.
Samotný deň sa potom otvorí ako filter `date=YYYY-MM-DD`.

---

## 2. Epizódy relácie (JSON)

`GET /json/tv/archiv?e=1&archive=1&s={showId}&p={strana}&l={na stranu}&o=desc[&d=YYYY-MM]`

* `s` = **showId** (`data-series-id`). Vráti epizódy zo všetkých sérií relácie.
* `d` je voliteľné. **Bez `d` vráti všetky mesiace** (Duel: `results: 2173`), stránkované cez `p` a `l`.
  `o=desc` = najnovšie hore. Web používa `l=1000`.
* `d=YYYY-MM` obmedzí výsledok na mesiac. Pre reláciu, ktorá v danom mesiaci nevysielala, vráti prázdny zoznam.

```json
{"paging":{"page":"2","size":"5","results":"2173"},
 "program":[{"ID":629324,"name":"Duel","air":"2026-11-10 17:45:00","last_reprise":"…",
             "synopsis":"\nVedomostná…","description":"","subtitle":"","image":"https://…jpg",
             "series":22948,"video_quality":"HD","accessibility_cc":"Y","audio_mode":"STEREO",
             "status_premiere":"Y","rating_kids":"N","authoring_eu":"Y", …}]}
```

**showId vs. series:** `series` je produkčná séria (sezóna). Jedna relácia ich má viac
(Duel 14126 → 19831, 18761, 22042, 22948, 21052, 17055…). Aj `s={series}` funguje, ale vráti len
tú jednu sériu (22948 → 153 epizód). Doplnok preto vždy používa showId.

**Epizódy jedného dňa (všetky relácie):** `d=YYYY-MM-DD` bez `s`
(napr. 17. 11. 2026 → 48 epizód; `o=asc` = chronologicky). Doplnok to používa v Kalendári.
Položky nemajú showId, len `series`; „ďalšie epizódy“ sa preto otvárajú cez `s={series}`.

Pole `license` (`"2026-12-01 23:59:59"` alebo prázdne) je dátum, dokedy je epizóda v archíve.

Zoznam epizód **neobsahuje dĺžku**. Tá je len v detaile (`archive5f.json`, pole `length`).

---

## 3. Detail a stream epizódy (JSON)

`GET /json/archive5f.json?id={episodeId}`

```json
{"IP":"…","request":"r5Fh0BAm",
 "clip":{"title":"Duel","description":"\n…","length":"00:29:21","image":"https://…png",
         "mediaid":"193112","datetime_create":"2026-11-13 17:56","backend":"e1",
         "subtitles":{"tracks":[{"lang":"sk","label":"Slovensky","id":185390,
              "src":"https://www.stvr.sk/plain/webvtt/video_captions.vtt?id=185390&__lng=sk"}]},
         "sources":[{"type":"application/x-mpegurl","src":"https://n11.stv.livebox.sk/stv-tv-arch/_definst_/smil:a510/…/00185390.smil/playlist.m3u8?auth=b64%3A…"},
                    {"type":"application/dash+xml","src":"https://e7.stv.livebox.sk/…/manifest.mpd?auth=…"}]}}
```

* Neexistujúce ID: odpoveď obsahuje iba `{"IP": "…"}` (bez `clip`). Nečíselné ID: HTTP 404.
* `auth` = `b64:` + base64(`{cesta}|{unix expiry}|{sha1}`), platnosť asi 2 h.
  **Stream URL sa preto nikdy nekešuje**, ale získava sa pri každom spustení.
* HLS master (`playlist.m3u8`) obsahuje absolútne URL variantov 1280x720, 1920x1080, 852x480 a 640x360
  (`…/vod/stv-tv-arch/{hash}/…/00185390-{1..4}.mp4/chunklist-v1-a1.m3u8`).
  Doplnok z neho pri nastavenej max. kvalite vyberie variant.
* Bez DRM. Bez `Referer` funguje.
* Aj staré epizódy (2021) majú zdroje.

### Geoblokácia
Zo SK IP sa nedala reprodukovať, preto ju doplnok rozpoznáva defenzívne:
* chýbajúci `clip` alebo prázdne `sources` → „Video nie je dostupné (mimo SR alebo vypršala licencia)“;
* HTTP 403/451 z ľubovoľného endpointu → hláška o geoblokácii.
Doplnok geoblokáciu nijako neobchádza.

---

## 4. Vyhľadávanie (JSON)

### Lite (našepkávač)
`GET /json/search/lite?q={dotaz}` (min. 3 znaky)

```json
{"total":"3","blocks":{
  "video_series":{"title":"TV relácie","total":"3","more":0,
     "hits":[{"score":"7.38","name":"Duel","name_hl":"<em>Duel</em>",
              "uri":"https://www.stvr.sk/televizia/archiv/14126/630608",
              "description":"…","thumbnail":"https://…jpg"}]}}}
```

Ďalšie bloky podľa dotazu: `page` (Weby), `audio_series` (Rádio relácie),
`video_live`, `audio_live` (Vysielame). Lite vracia max. 3 položky na blok (`more` = koľko ešte je).

### Full
`GET /json/search/full?q={dotaz}&s={blok}&o={offset}[&r={od},{do}]`

* `s` = zdroj (`video_series`, `audio_series`, `sites`, `news`, `article`, `video_live`, `audio_live`).
* `o` = offset, 20 výsledkov na stranu, `more` = koľko zostáva.
* Hity navyše obsahujú `latest_episode_uri`, `next_airing_p`.
* **Pozor:** niektoré hity majú `uri` `/televizia/program/{id}` a prázdne `latest_episode_uri`.
  Sú to relácie bez archívu, doplnok ich vynecháva.

---

## 5. Ostatné
* `/bs/json/ima?target.s=…` – reklamy (IMA) pre webový prehrávač, nepotrebné.
* `/json/read.json`, `/json/exkurzia_sro_slots`, `/bs/json/get` – nesúvisia s archívom.
* `/embed/archive/{showId}/{episodeId}` – embed prehrávača.
