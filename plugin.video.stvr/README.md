# STVR archív (neoficiálny) – doplnok pre Kodi

Doplnok `plugin.video.stvr` prehráva [archív STVR](https://www.stvr.sk/televizia/archiv)
(Jednotka, Dvojka, :24, Šport) a jej živé vysielanie priamo v Kodi, teda aj na televízore
(Chromecast s Google TV, Android TV, PC…).

> Doplnok nie je oficiálny a nie je nijako spojený so STVR. Používa rovnaké verejné
> rozhranie ako web stvr.sk. Obsah je dostupný len zo Slovenska a doplnok geoblokáciu
> neobchádza. Videá sa nesťahujú, iba prehrávajú.

## Čo vie

* **Naživo**: 7 kanálov (Jednotka, Dvojka, :24, Šport, Live O, Live STVR, NR SR)
  s práve vysielaným programom, až do 1080p
* **Žánre** s podžánrami (Filmy, Seriály, Zábava → Varenie, …)
* **A–Z**, **Kanály**, **Pre deti**, **Európska tvorba**: rovnaké filtre ako na webe
* **Kalendár**: dni vysielania, pri každom dni program s prehrateľnými epizódami
* **Hľadať** s históriou hľadaných výrazov
* **Pozrieť neskôr**: relácie aj epizódy, pridávajú sa cez kontextové menu
  (dlhé stlačenie OK / pravé tlačidlo myši)
* Epizódy so dátumom vysielania, popisom, obrázkom, dĺžkou a dátumom „dostupné do“
* Slovenské titulky (ak ich epizóda má)
* Kodi si pamätá pozíciu prehrávania a pozreté epizódy

## Inštalácia

Doplnok potrebuje **Kodi 20 alebo novšie** (testované na Kodi 21 Omega). Inštaluje sa
z repozitára **Magrathea Repository** (návod je v [hlavnom README](../README.md#inštalácia)),
Kodi ho potom aktualizuje samo:
*Inštalovať z repozitára → Magrathea Repository → Video doplnky → STVR archív (neoficiálny)*.

## Nastavenia

| Nastavenie | Význam |
|---|---|
| Maximálna kvalita | Najlepšia / 1080p / 720p / 480p / 360p. Pri pomalej sieti zvoľte nižšiu. |
| Načítať titulky | Pripojí slovenské titulky (zapnúť ich treba v prehrávači). |
| Použiť InputStream Adaptive | Prehrávanie cez doplnok *InputStream Adaptive* (HLS alebo DASH, adaptívna kvalita). Voliteľné, bez neho to funguje tiež. |
| Počet epizód na stranu | Koľko epizód sa zobrazí naraz (položka *Staršie…* načíta ďalšie). |
| Zobrazovať dĺžku epizód | Dĺžka nie je v zozname epizód, doplnok ju zisťuje zvlášť (raz, potom sa pamätá). Vypnutím sa zoznamy načítajú rýchlejšie. |
| Platnosť medzipamäte | Ako dlho sa pamätajú zoznamy (stream sa nepamätá nikdy). |

## Vývoj

Doplnok používa len štandardnú knižnicu Pythonu 3. Všetko, čo závisí od webu STVR,
je v [`resources/lib/api.py`](resources/lib/api.py). Popis rozhrania je v
[`docs/API.md`](docs/API.md). Príkazy sa spúšťajú z koreňa repozitára:

```bash
pip install pytest
python -m pytest                                   # offline testy (fixtures)
STVR_LIVE=1 python -m pytest tests/test_live.py    # proti skutočnému API (zo SK IP)
```

Router sa dá spustiť bez Kodi (stuby `xbmc*` sú v `dev/stubs/`):

```bash
python dev/run.py                                            # hlavné menu
python dev/run.py "plugin://plugin.video.stvr/?action=genres"
python dev/run.py "?action=show&id=14126&title=Duel" --details
python dev/run.py "?action=play&id=630571" --set max_quality=2
python dev/run.py "?action=search_new" --input duel
```

`python dev/gen_strings.py` vygeneruje `strings.po` (sk/en) z jedného zoznamu.

## Licencia

[GPL-2.0-or-later](LICENSE.txt)
