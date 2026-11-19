# -*- coding: utf-8 -*-
"""Vygeneruje resources/language/*/strings.po z jedného zoznamu (sk + en)."""
import io
import os

STRINGS = [
    (30000, "Genres", "Žánre"),
    (30001, "A–Z", "A–Z"),
    (30002, "Channels", "Kanály"),
    (30003, "Calendar", "Kalendár"),
    (30004, "Search", "Hľadať"),
    (30005, "Watch later", "Pozrieť neskôr"),
    (30006, "For kids", "Pre deti"),
    (30007, "European works", "Európska tvorba"),
    (30008, "Live", "Naživo"),
    (30010, "Subgenres…", "Podžánre…"),
    (30012, "Next page…", "Ďalšia strana…"),
    (30013, "Older…", "Staršie…"),
    (30014, "Previous month (%s)", "Predchádzajúci mesiac (%s)"),
    (30015, "New search…", "Nové hľadanie…"),
    (30016, "Search term (at least 3 characters)", "Hľadaný výraz (aspoň 3 znaky)"),
    (30017, "Remove from history", "Odstrániť z histórie"),
    (30018, "Clear search history", "Vymazať históriu hľadania"),
    (30019, "Add to Watch later", "Pridať do Pozrieť neskôr"),
    (30020, "Remove from Watch later", "Odobrať z Pozrieť neskôr"),
    (30021, "Added to Watch later", "Pridané do Pozrieť neskôr"),
    (30022, "Removed from Watch later", "Odobrané z Pozrieť neskôr"),
    (30023, "The list is empty", "Zoznam je prázdny"),
    (30024, "Nothing found", "Nič sa nenašlo"),
    (30025, "Go to show", "Otvoriť reláciu"),
    (30027, "Available until %s", "Dostupné do %s"),
    (30030, "Could not load data from STVR", "Nepodarilo sa načítať údaje zo STVR"),
    (30031, "This video is not available. It may be available only in Slovakia or its licence has expired.",
            "Video nie je dostupné. Možno je dostupné len na Slovensku alebo mu vypršala licencia."),
    (30032, "STVR content is only available from Slovakia (geo-blocking).",
            "Obsah STVR je dostupný len zo Slovenska (geoblokácia)."),
    (30033, "Cache cleared", "Medzipamäť vymazaná"),
    (30034, "Enter at least 3 characters", "Zadajte aspoň 3 znaky"),
    (30100, "Playback", "Prehrávanie"),
    (30101, "Use InputStream Adaptive", "Použiť InputStream Adaptive"),
    (30102, "Play through the InputStream Adaptive add-on (adaptive quality). It must be installed.",
            "Prehrávať cez doplnok InputStream Adaptive (adaptívna kvalita). Musí byť nainštalovaný."),
    (30103, "Stream format", "Formát streamu"),
    (30104, "HLS", "HLS"),
    (30105, "DASH", "DASH"),
    (30106, "Maximum quality", "Maximálna kvalita"),
    (30107, "Best available", "Najlepšia dostupná"),
    (30108, "1080p", "1080p"),
    (30109, "720p", "720p"),
    (30110, "480p", "480p"),
    (30111, "360p", "360p"),
    (30112, "Load subtitles", "Načítať titulky"),
    (30113, "Applies to HLS playback without InputStream Adaptive.",
            "Platí pre prehrávanie HLS bez InputStream Adaptive."),
    (30114, "InputStream Adaptive", "InputStream Adaptive"),
    (30120, "General", "Všeobecné"),
    (30121, "Episodes per page", "Počet epizód na stranu"),
    (30122, "Show episode durations", "Zobrazovať dĺžku epizód"),
    (30123, "List cache lifetime (minutes)", "Platnosť medzipamäte zoznamov (minúty)"),
    (30124, "Clear cache", "Vymazať medzipamäť"),
    (30125, "Needs one extra request per episode (cached afterwards), lists load a bit slower.",
            "Pre každú epizódu je potrebná jedna požiadavka navyše (potom sa pamätá), zoznamy sa načítajú pomalšie."),
    (30200, "Mon", "Po"),
    (30201, "Tue", "Ut"),
    (30202, "Wed", "St"),
    (30203, "Thu", "Št"),
    (30204, "Fri", "Pi"),
    (30205, "Sat", "So"),
    (30206, "Sun", "Ne"),
]

HEADER = r'''# Kodi Media Center language file
# Addon Name: STVR archív (neoficiálny)
# Addon id: plugin.video.stvr
# Addon Provider: tvadovic
# Vygenerované z dev/gen_strings.py – needitovať ručne.
msgid ""
msgstr ""
"Project-Id-Version: plugin.video.stvr\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Language: {lang}\n"
"Plural-Forms: nplurals=3; plural=(n==1) ? 0 : (n>=2 && n<=4) ? 1 : 2;\n"
'''


def esc(text):
    return text.replace("\\", "\\\\").replace('"', '\\"')


def main():
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugin.video.stvr", "resources", "language")
    for folder, lang, column in (("resource.language.en_gb", "en_GB", 1), ("resource.language.sk_sk", "sk_SK", 2)):
        lines = [HEADER.format(lang=lang)]
        if lang == "en_GB":
            lines[0] = lines[0].replace("nplurals=3; plural=(n==1) ? 0 : (n>=2 && n<=4) ? 1 : 2;", "nplurals=2; plural=(n != 1);")
        for row in STRINGS:
            msgstr = "" if lang == "en_GB" else row[column]
            lines.append('msgctxt "#%d"\nmsgid "%s"\nmsgstr "%s"\n' % (row[0], esc(row[1]), esc(msgstr)))
        path = os.path.join(root, folder)
        if not os.path.isdir(path):
            os.makedirs(path)
        with io.open(os.path.join(path, "strings.po"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines))


if __name__ == "__main__":
    main()
