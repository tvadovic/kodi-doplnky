# Trakt.tv (Stream Cinema) – neoficiálna oprava pre Kodi

Doplnok `script.streamcinema.traktfix` vracia do doplnku
[Stream Cinema CZ a SK](https://github.com/bbaronSVK/plugin.video.stream-cinema) funkčné
prepojenie s [Trakt.tv](https://trakt.tv): zoznamy filmov a seriálov z Traktu sa znova
spárujú so streamami v Stream Cinema a dajú sa prehrať.

> Doplnok nie je oficiálny a nie je nijako spojený s autormi Stream Cinema ani s Trakt.tv.
> Keď autori Stream Cinema problém opravia u seba, tento doplnok už nebude treba.

## O čo ide

Do novembra 2026 server Stream Cinema (API 2.0):

* prestal v hlavnom menu posielať priečinok **Trakt.tv**,
* zrušil rozhrania `/Search/getTrakt` a `/Last` (HTTP 404), cez ktoré doplnok zoznamy
  z Traktu prekladal na položky Stream Cinema. Každý zoznam končil hláškou
  *Connection error*.

Prihlásenie do Traktu aj prehrávanie pritom fungujú ďalej. Funkčné zostalo aj rozhranie
`/Ftrakt2sc`, ktoré prekladá Trakt ID na ID Stream Cinema.

Oprava upravuje dva súbory Stream Cinema
(`resources/lib/trakt/Trakt.py` a `api.py`):

* položky zoznamov sa skladajú priamo v doplnku: Trakt ID → `/Ftrakt2sc` → film
  (`/Play/<id>`) alebo seriál (`/FGet/<id>`),
* popis, žánre, hodnotenie, dĺžka, trailer a obrázky (plagát, fanart, logo) sa berú
  z Traktu (`extended=full,images`); popis je preto po anglicky,
* opravené sú aj chyby pôvodného kódu v pohľadoch **História** a **Rozpozerané**
  (pád pri seriáloch, prázdna história filmov, duplicitné položky),
* späť je kontextové menu **Trakt.tv zoznamy**. Staršie verzie Stream Cinema (1.x) ho mali
  ako „Trakt menu“, v 2.x pri prepise vypadlo.

Funguje: vlastné zoznamy, watchlist, zoznamy a watchlisty priateľov a sledovaných,
história filmov a seriálov, rozpozerané. Položky, ktoré Stream Cinema vo svojej
databáze nemá, sa vynechajú.

## Ako to funguje

* **Pri štarte Kodi** (služba) doplnok skontroluje odtlačok SHA-256 oboch súborov
  v nainštalovanom Stream Cinema:
  * pôvodná známa verzia → nahradí ich opravenými (originál uloží ako `*.orig`),
  * už opravené → nič,
  * **iná verzia** (Stream Cinema sa aktualizoval) → **nič neprepíše**, iba upozorní.
    Novú verziu Stream Cinema teda nepoškodí. Kým nevyjde nová verzia opravy,
    Trakt v Stream Cinema nebude fungovať.
* **Kontextové menu** (dlhé stlačenie OK) na filme alebo seriáli kdekoľvek v Stream Cinema
  má položku **Trakt.tv zoznamy**:
  * zobrazí watchlist a vlastné zoznamy, kde je položka už zaškrtnutá,
  * zaškrtnutím ju pridáš, odškrtnutím odoberieš,
  * *+ Nový zoznam…* vytvorí súkromný zoznam a pridá ju doň.
* **Spustenie doplnku** otvorí priečinok Trakt.tv v Stream Cinema. Ten v hlavnom menu
  Stream Cinema chýba, preto je dobré pridať si doplnok do **Obľúbených**.

Automatické aktualizácie Stream Cinema netreba vypínať. Po aktualizácii, ktorá tieto
súbory nezmení, sa oprava pri ďalšom štarte Kodi nahrá znova.

Podporované verzie Stream Cinema: **2.6.10.3+k19**.

## Inštalácia

Doplnok je v repozitári **Magrathea Repository** (návod na jeho pridanie je v
[hlavnom README](../README.md#inštalácia)).

1. *Doplnky → Prehliadač doplnkov → Inštalovať z repozitára → Magrathea Repository →
   Video doplnky → Trakt.tv (Stream Cinema) → Inštalovať*.
2. Objaví sa hlásenie *Oprava Trakt nahraná*. **Reštartuj Kodi**
   (na Android TV: *Nastavenia → Aplikácie → Kodi → Vynútiť zastavenie*).
3. *Doplnky → Video doplnky → Trakt.tv (Stream Cinema)* → kontextové menu
   (dlhé stlačenie OK) → **Pridať do obľúbených**.
4. Ak priečinok hlási chybu prihlásenia: *Stream Cinema → Nastavenia → Trakt → Prihlásiť*.

### Odinštalovanie
Odinštaluj tento doplnok a v priečinku
`addons/plugin.video.stream-cinema/resources/lib/trakt/` premenuj `Trakt.py.orig`
a `api.py.orig` späť (alebo Stream Cinema preinštaluj).

## Podpora novej verzie Stream Cinema

1. Do `resources/patch/` daj opravené `Trakt.py` a `api.py` pre novú verziu
   (`.gitattributes` ich necháva bajt po bajte, test overí konce riadkov LF ako v originále).
2. Do `ORIGINALS` v [`resources/lib/patcher.py`](resources/lib/patcher.py) pridaj
   SHA-256 pôvodných súborov novej verzie. Pri akejkoľvek zmene súboru v `resources/patch/`
   tam pridaj aj odtlačok jeho predchádzajúcej opravenej verzie. Inak by nainštalovaná
   oprava hlásila „iná verzia“ a neaktualizovala sa.
3. Zvýš `version` a `news` v [`addon.xml`](addon.xml) a pushni do `main`. GitHub Action
   doplnok zabalí a zverejní v repozitári, Kodi si ho stiahne samo.

## Licencia

[GPL-3.0](LICENSE.txt), rovnako ako Stream Cinema, z ktorého pochádzajú upravené súbory
v `resources/patch/`.
