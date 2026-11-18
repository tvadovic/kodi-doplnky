# STVR archív (neoficiálny) – doplnok pre Kodi

Doplnok `plugin.video.stvr` prehráva [archív STVR](https://www.stvr.sk/televizia/archiv)
(Jednotka, Dvojka, :24, Šport) priamo v Kodi, teda aj na televízore
(Chromecast s Google TV, Android TV, PC…).

> Doplnok nie je oficiálny a nie je nijako spojený so STVR. Používa rovnaké verejné
> rozhranie ako web stvr.sk. Obsah je dostupný len zo Slovenska a doplnok geoblokáciu
> neobchádza. Videá sa nesťahujú, iba prehrávajú.

## Čo vie

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

Doplnok potrebuje **Kodi 20 alebo novšie** (testované na Kodi 21 Omega).
Nemá žiadne závislosti.

1. Stiahnite si `plugin.video.stvr-X.Y.Z.zip` z
   [Releases](https://github.com/tvadovic/plugin.video.stvr/releases/latest).
2. V Kodi zapnite inštaláciu z neznámych zdrojov:
   *Nastavenia → Systém → Doplnky → Neznáme zdroje* (zapnúť).

### PC (Windows, Linux, macOS)
3. *Doplnky → ikona otvorenej krabice (Prehliadač doplnkov) → Inštalovať zo súboru ZIP*
   a vyberte stiahnutý ZIP.
4. Doplnok nájdete v *Doplnky → Video doplnky → STVR archív (neoficiálny)*.

### Chromecast s Google TV / Android TV
Na TV je najťažšie dostať tam ZIP súbor. Možnosti:

* **Aplikácia Downloader** (Google Play): do adresy zadajte odkaz na ZIP z Releases.
  Stiahne ho do priečinka *Download*. V Kodi potom *Inštalovať zo súboru ZIP → External storage → Download*.
* **Zdieľaný priečinok v sieti**: v Kodi *Súbory → Pridať zdroj* s cestou
  `smb://…` k priečinku s ZIP-om na PC, potom *Inštalovať zo súboru ZIP* z tohto zdroja.
* **USB kľúč** cez OTG adaptér.

Neskôr pribudne vlastný Kodi repozitár. Potom stačí pridať jednu URL ako zdroj
a doplnok sa bude aktualizovať sám.

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
[`docs/API.md`](docs/API.md).

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

Ďalšie nástroje:
* `python dev/build_zip.py`: zabalí `dist/plugin.video.stvr-<verzia>.zip`
* `python dev/gen_strings.py`: vygeneruje `strings.po` (sk/en) z jedného zoznamu
* `dev/make_art.ps1`: vygeneruje `icon.png` a `fanart.jpg`

### Vydanie novej verzie
1. Zvýšte `version` (a `news`) v `addon.xml`.
2. `git tag v0.2.0 && git push --tags`
3. GitHub Action spustí testy, zabalí ZIP a pridá ho do Release.
   Ak tag nesedí s verziou v `addon.xml`, build zlyhá.

## Licencia

[GPL-2.0-or-later](LICENSE.txt)
