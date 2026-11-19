# Kodi doplnky – Magrathea Repository

Neoficiálne doplnky pre [Kodi](https://kodi.tv) a ich repozitár **Magrathea Repository**.
Fungujú na PC aj na televízore (Chromecast s Google TV, Android TV…). Z repozitára
ich Kodi aktualizuje samo.

| Doplnok | Čo robí |
|---|---|
| [**STVR archív (neoficiálny)**](plugin.video.stvr/README.md)<br>`plugin.video.stvr` | Archív a živé vysielanie STVR (Jednotka, Dvojka, :24, Šport…) |
| [**Trakt.tv (Stream Cinema)**](script.streamcinema.traktfix/README.md)<br>`script.streamcinema.traktfix` | Neoficiálna oprava Trakt.tv v doplnku Stream Cinema CZ a SK: zoznamy, watchlist, história a kontextové menu na pridávanie do zoznamov |
| [**Magrathea Repository**](repository.tvadovic/addon.xml)<br>`repository.tvadovic` | Repozitár, z ktorého sa doplnky inštalujú a aktualizujú |

> Doplnky nie sú oficiálne a nie sú spojené so STVR, autormi Stream Cinema ani s Trakt.tv.

## Inštalácia

Doplnky potrebujú **Kodi 20 alebo novšie** (testované na Kodi 21 Omega).
Postup je rovnaký na PC aj na TV.

1. **Povoliť neznáme zdroje:** *Nastavenia → Systém → Doplnky → Neznáme zdroje* (zapnúť, potvrdiť).
2. **Pridať zdroj:** *Nastavenia → Správca súborov → Pridať zdroj → &lt;Žiadne&gt;*, zadajte URL

   ```
   https://tvadovic.github.io/kodi-doplnky/
   ```

   a ako názov napr. `magrathea` → *OK*.
3. **Nainštalovať repozitár:** *Doplnky → ikona otvorenej krabice (Prehliadač doplnkov) →
   Inštalovať zo súboru ZIP → magrathea → `repository.tvadovic-X.Y.Z.zip`*.
4. **Nainštalovať doplnok:** v tom istom menu *Inštalovať z repozitára → Magrathea Repository →
   Video doplnky →* vybraný doplnok *→ Inštalovať*.

Na Chromecaste s Google TV alebo Android TV nainštalujte Kodi z Google Play a postupujte rovnako.
Nič netreba sťahovať ani kopírovať, jediná práca navyše je napísať URL zdroja ovládačom.

**Ručne zo ZIP** (bez automatických aktualizácií): ZIP každej verzie je aj v
[Releases](https://github.com/tvadovic/kodi-doplnky/releases).

## Štruktúra a vývoj

Každý doplnok je priečinok s `addon.xml` v koreni repozitára. Spoločné sú:

* `tests/`: testy všetkých doplnkov (`pip install pytest && python -m pytest`)
* `dev/build_zip.py`: zabalí doplnok do `dist/{id}-{verzia}.zip`
  (`--addon <priečinok>`, `--all` = všetky; `docs/`, `tests/` a `__pycache__` sa nebalia)
* `dev/build_repo.py dist/*.zip --out <checkout gh-pages>`: poskladá Kodi repozitár
  (`addons.xml`, `.md5`, ZIP-y, ikony a `index.html` pre Kodi)
* `dev/make_art.ps1`: vygeneruje ikony a fanart všetkých doplnkov
* `dev/run.py`, `dev/stubs/`, `dev/gen_strings.py`: nástroje pre STVR archív
  (pozri jeho [README](plugin.video.stvr/README.md#vývoj))

### Vydanie novej verzie
1. Zvýšte `version` (a `news`) v `addon.xml` doplnku.
2. Zlúčte zmenu do `main`.
3. Workflow *Zverejnenie* spustí testy, zabalí všetky doplnky, nové verzie pridá do Kodi
   repozitára na vetve `gh-pages` (GitHub Pages) a vytvorí pre ne GitHub Release
   s tagom `{id}-{verzia}`. Kodi si novú verziu stiahne samo.

Zverejnená verzia sa neprepisuje. Zmena bez zvýšenia `version` sa do Kodi nedostane.

## Licencia

* STVR archív, repozitár a nástroje: [GPL-2.0-or-later](LICENSE.txt)
* Trakt.tv (Stream Cinema): [GPL-3.0](script.streamcinema.traktfix/LICENSE.txt),
  rovnako ako Stream Cinema, z ktorého pochádzajú upravené súbory
