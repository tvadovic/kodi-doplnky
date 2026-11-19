# -*- coding: utf-8 -*-
"""Kontextové menu na položke Stream Cinema: Trakt.tv zoznamy (pridať/odobrať)."""
import sys
from binascii import hexlify

import xbmc


def _hex(value):
    # Stream Cinema skúša dekódovať každý parameter z hex; nehex hodnota (napr. 4810)
    # by sa dekódovala na nezmysel
    return hexlify('{}'.format(value).encode('utf-8')).decode('ascii')


def main():
    item = sys.listitem
    tag = item.getVideoInfoTag()
    args = {
        'action': 'trakt.manager',
        'content': 'movie' if tag.getMediaType() == 'movie' else 'tvshow',
        'title': tag.getTitle() or item.getLabel(),
    }
    for key in ('trakt', 'imdb', 'tmdb', 'tvdb'):
        value = tag.getUniqueID(key)
        if value:
            args[key] = value
    query = '&'.join('{}={}'.format(k, _hex(v)) for k, v in args.items())
    xbmc.executebuiltin('RunPlugin(plugin://plugin.video.stream-cinema/?{})'.format(query))


if __name__ == '__main__':
    main()
