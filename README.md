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

Doplnok potrebuje **Kodi 20 alebo novšie** (testované na Kodi 21 Omega).
Najjednoduchšie je nainštalovať ho z repozitára, Kodi ho potom **aktualizuje samo**.
Postup je rovnaký na PC aj na TV.

1. **Povoliť neznáme zdroje:** *Nastavenia → Systém → Doplnky → Neznáme zdroje* (zapnúť, potvrdiť).
2. **Pridať zdroj:** *Nastavenia → Správca súborov → Pridať zdroj → &lt;Žiadne&gt;*, zadajte URL

   ```
   https://tvadovic.github.io/plugin.video.stvr/
   ```

   a ako názov napr. `tvadovic` → *OK*.
3. **Nainštalovať repozitár:** *Doplnky → ikona otvorenej krabice (Prehliadač doplnkov) →
   Inštalovať zo súboru ZIP → tvadovic → `repository.tvadovic-X.Y.Z.zip`*.
4. **Nainštalovať doplnok:** v tom istom menu *Inštalovať z repozitára → Magrathea Repository →
   Video doplnky → STVR archív (neoficiálny) → Inštalovať*.

Doplnok nájdete v *Doplnky → Video doplnky → STVR archív (neoficiálny)*.

### Chromecast s Google TV / Android TV
Kodi nainštalujte z Google Play a postupujte podľa krokov vyššie. Nič netreba sťahovať
ani kopírovať, jediná práca navyše je napísať URL zdroja ovládačom.

### Ručne zo ZIP (bez automatických aktualizácií)
`plugin.video.stvr-X.Y.Z.zip` je aj v
[Releases](https://github.com/tvadovic/plugin.video.stvr/releases/latest).
Nainštalujete ho cez *Inštalovať zo súboru ZIP*, novšie verzie si však treba sťahovať ručne.

### Ďalšie doplnky v repozitári
* **Trakt.tv (Stream Cinema)**: neoficiálna oprava prepojenia Stream Cinema CZ a SK
  s Trakt.tv (zoznamy, watchlist, história). Popis a inštalácia:
  [`script.streamcinema.traktfix/`](script.streamcinema.traktfix/README.md).

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
  (`--addon repository.tvadovic` zabalí repozitár doplnkov)
* `python dev/build_repo.py dist/*.zip --out <checkout gh-pages>`: poskladá Kodi repozitár
  (`addons.xml`, `.md5`, ZIP-y, ikony a `index.html` pre Kodi)
* `python dev/gen_strings.py`: vygeneruje `strings.po` (sk/en) z jedného zoznamu
* `dev/make_art.ps1`: vygeneruje `icon.png`, `fanart.jpg`, ikonu repozitára a ikonu opravy Trakt

### Vydanie novej verzie
1. Zvýšte `version` (a `news`) v `addon.xml`.
2. `git tag v0.2.0 && git push --tags`
3. GitHub Action spustí testy, zabalí ZIP, pridá ho do Release a aktualizuje Kodi
   repozitár na vetve `gh-pages` (GitHub Pages). Kodi si novú verziu stiahne samo.
   Ak tag nesedí s verziou v `addon.xml`, build zlyhá.

Repozitár doplnkov **Magrathea Repository** je v [`repository.tvadovic/`](repository.tvadovic/addon.xml).
On aj [`script.streamcinema.traktfix/`](script.streamcinema.traktfix/) sa zverejnia po pushi do `main`
(workflow *Repozitár*). Pri zmene zvýšte ich `version`, inak zostane zverejnený starý ZIP
(rovnaká verzia sa neprepisuje).

## Licencia

[GPL-2.0-or-later](LICENSE.txt)
