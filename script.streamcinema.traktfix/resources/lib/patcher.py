# -*- coding: utf-8 -*-
"""
Nahradí Trakt.py a api.py v plugin.video.stream-cinema opravenými verziami
z resources/patch/.

Súbor sa prepíše len vtedy, keď je v presne známom stave (SHA-256 v ORIGINALS):
pôvodný zo Stream Cinema alebo opravený staršou verziou tohto doplnku. Ak ho
aktualizácia Stream Cinema zmenila, nič sa neprepíše, aby sa nepoškodil.

Podpora novej verzie Stream Cinema: pridaj SHA-256 jej pôvodných súborov
do ORIGINALS, oprav súbory v resources/patch/ a zvýš verziu v addon.xml.
Pri zmene súboru v resources/patch/ pridaj do ORIGINALS odtlačok predchádzajúcej
opravenej verzie, inak sa nainštalovaná oprava neaktualizuje.
"""
import hashlib
import os
import shutil

# súbor -> SHA-256 známych verzií, ktoré sa smú prepísať (plugin.video.stream-cinema)
ORIGINALS = {
    'Trakt.py': {
        '13c4fe49965aadd2cc53aea54aff8b7c032de45ab528ec7a8484dd630fbc2c21',  # 2.6.10.3+k19
        '9d79564ae6d6d05780f6cc71cd8fd94bc53006f384f7135df974e45602ecd38e',  # oprava 1.0.1
    },
    'api.py': {
        '83b820046747a1bc645cbd627c36dce4956bffc91baa259a20cc4ed2e4e97df1',  # 2.6.10.3+k19
    },
}

PATCHED = 'patched'      # už bolo opravené skôr
APPLIED = 'applied'      # opravené práve teraz (treba reštart Kodi)
UNKNOWN = 'unknown'      # neznáma verzia súborov, nič sa nezmenilo
MISSING = 'missing'      # Stream Cinema nie je nainštalované


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def apply(target_dir, patch_dir, originals=ORIGINALS):
    """target_dir = .../plugin.video.stream-cinema/resources/lib/trakt"""
    if not os.path.isdir(target_dir):
        return MISSING

    # najprv over všetky súbory, až potom zapisuj (nikdy nie polovičná oprava)
    todo = []
    for name, known in originals.items():
        path = os.path.join(target_dir, name)
        if not os.path.isfile(path):
            return UNKNOWN
        cur = sha256(path)
        if cur == sha256(os.path.join(patch_dir, name)):
            continue
        if cur not in known:
            return UNKNOWN
        todo.append(name)

    if not todo:
        return PATCHED

    for name in todo:
        path = os.path.join(target_dir, name)
        backup = path + '.orig'
        if not os.path.exists(backup):
            shutil.copy2(path, backup)
        tmp = path + '.new'
        shutil.copyfile(os.path.join(patch_dir, name), tmp)
        os.replace(tmp, path)
    return APPLIED
