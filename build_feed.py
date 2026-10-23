#!/usr/bin/env python3
"""Merge four podcast feeds into one standards-oriented podcast RSS feed."""
import copy
import datetime as dt
import email.utils
import json
import os
from pathlib import Path
import sys
import urllib.request
import xml.etree.ElementTree as ET

ITUNES = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
ATOM = 'http://www.w3.org/2005/Atom'
CONTENT = 'http://purl.org/rss/1.0/modules/content/'
ET.register_namespace('itunes', ITUNES)
ET.register_namespace('atom', ATOM)
ET.register_namespace('content', CONTENT)

SOURCES = [
    ('CEPOS – Bag om Nyhederne', 'https://anchor.fm/s/fb93118c/podcast/rss'),
    ('Borgerlig Tabloid', 'https://www.omnycontent.com/d/playlist/1283f5f4-2508-4981-a99f-acb500e64dcf/a8df889a-1ef0-40fd-94bb-af1e00cff416/89869564-4bca-4df0-bca3-af1e00d05284/podcast.rss'),
    ('Liberal Alliance', 'https://feed.podbean.com/liberalalliance/feed.xml'),
    ('Supertrends', 'https://www.spreaker.com/show/5768334/episodes/feed'),
]

OUT = Path('docs')
MAX_EPISODES = int(os.getenv('MAX_EPISODES', '0'))  # 0 = all available episodes

def sub(parent, tag, value):
    el = ET.SubElement(parent, tag)
    el.text = str(value)
    return el

def get_text(el, name, default=''):
    x = el.find(name)
    return (x.text or '').strip() if x is not None else default

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'PodcastFeedMerge/1.0 (+GitHub Actions)', 'Accept': 'application/rss+xml, application/xml, text/xml, */*'})
    with urllib.request.urlopen(req, timeout=75) as response:
        return response.read()

def parsedate(value):
    try:
        d = email.utils.parsedate_to_datetime(value)
        return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
    except (TypeError, ValueError, IndexError):
        return None

def main():
    repo = os.environ.get('GITHUB_REPOSITORY', 'YOUR_USERNAME/podcast-github')
    owner, _, name = repo.partition('/')
    base = f'https://{owner.lower()}.github.io/{name}/'
    url = base + 'podcast.xml'
    collected = []
    errors = []
    first_cover = ''
    for label, source in SOURCES:
        try:
            root = ET.fromstring(fetch(source))
            channel = root.find('channel')
            if channel is None:
                raise ValueError('Missing RSS channel')
            img = channel.find(f'{{{ITUNES}}}image')
            if not first_cover and img is not None:
                first_cover = img.get('href', '')
            for item in channel.findall('item'):
                enclosure = item.find('enclosure')
                if enclosure is None or not enclosure.get('url'):
                    continue
                title = get_text(item, 'title')
                pub = parsedate(get_text(item, 'pubDate'))
                if not title or pub is None:
                    continue
                guid = get_text(item, 'guid') or enclosure.get('url')
                # Preserve original GUID, qualified by source to avoid cross-feed collisions.
                key = source + '|' + guid
                collected.append((pub, label, key, item))
            print(f'Loaded {label}: {sum(x[1] == label for x in collected)} episodes')
        except Exception as exc:
            errors.append(f'{label}: {exc}')
            print(f'ERROR {label}: {exc}', file=sys.stderr)
    # Do not silently publish an incomplete feed if any source is unavailable.
    if errors:
        raise RuntimeError('Refusing to publish incomplete feed: ' + '; '.join(errors))
    if not collected:
        raise RuntimeError('No playable episodes found')
    collected.sort(key=lambda x: (x[0], x[2]), reverse=True)
    if MAX_EPISODES > 0:
        collected = collected[:MAX_EPISODES]

    rss = ET.Element('rss', {'version': '2.0'})
    ch = ET.SubElement(rss, 'channel')
    sub(ch, 'title', 'Mine fire danske podcasts')
    sub(ch, 'link', base)
    sub(ch, 'description', 'CEPOS Bag om Nyhederne, Borgerlig Tabloid, Liberal Alliance og Supertrends – samlet efter oprindelig udgivelsesdato.')
    sub(ch, 'language', 'da-DK')
    sub(ch, f'{{{ITUNES}}}author', 'Samlet podcastoversigt')
    sub(ch, f'{{{ITUNES}}}summary', 'Fire danske podcasts samlet i én kronologisk podcastoversigt.')
    sub(ch, f'{{{ITUNES}}}explicit', 'false')
    sub(ch, f'{{{ITUNES}}}type', 'episodic')
    sub(ch, f'{{{ITUNES}}}category', '').set('text', 'News')
    ET.SubElement(ch, f'{{{ATOM}}}link', {'href': url, 'rel': 'self', 'type': 'application/rss+xml'})
    if first_cover:
        ET.SubElement(ch, f'{{{ITUNES}}}image', {'href': first_cover})
        image = ET.SubElement(ch, 'image')
        sub(image, 'url', first_cover)
        sub(image, 'title', 'Mine fire danske podcasts')
        sub(image, 'link', base)
    else:
        raise RuntimeError('No channel-level podcast cover available from source feeds')
    sub(ch, 'lastBuildDate', email.utils.format_datetime(dt.datetime.now(dt.timezone.utc)))

    for pub, label, key, original in collected:
        item = ET.SubElement(ch, 'item')
        title = get_text(original, 'title')
        sub(item, 'title', f'[{label}] {title}')
        sub(item, 'description', get_text(original, 'description') or title)
        original_link = get_text(original, 'link')
        if original_link:
            sub(item, 'link', original_link)
        sub(item, 'pubDate', email.utils.format_datetime(pub))
        guid = sub(item, 'guid', key)
        guid.set('isPermaLink', 'false')
        orig_enclosure = original.find('enclosure')
        enc_attrs = {k: v for k, v in orig_enclosure.attrib.items() if k in ('url', 'length', 'type')}
        # Use original MIME type; do not mislabel AAC audio as MP3.
        if 'type' not in enc_attrs:
            enc_attrs['type'] = 'audio/mpeg' if enc_attrs['url'].lower().split('?')[0].endswith('.mp3') else 'audio/mp4'
        if 'length' not in enc_attrs:
            enc_attrs['length'] = '0'
        ET.SubElement(item, 'enclosure', enc_attrs)
        for tag in (f'{{{ITUNES}}}duration', f'{{{ITUNES}}}explicit', f'{{{ITUNES}}}episodeType', f'{{{ITUNES}}}image'):
            existing = original.find(tag)
            if existing is not None:
                item.append(copy.deepcopy(existing))
        sub(item, f'{{{ITUNES}}}author', label)

    OUT.mkdir(exist_ok=True)
    ET.indent(rss, space='  ')
    ET.ElementTree(rss).write(OUT / 'podcast.xml', encoding='utf-8', xml_declaration=True)
    (OUT / 'index.html').write_text('<!doctype html><html lang="da"><meta charset="utf-8"><title>Mine fire danske podcasts</title><h1>Mine fire danske podcasts</h1><p><a href="podcast.xml">Podcast RSS</a></p></html>', encoding='utf-8')
    (OUT / '.nojekyll').write_text('', encoding='utf-8')
    (OUT / 'status.json').write_text(json.dumps({'episodes': len(collected), 'updated_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'sources': len(SOURCES)}, indent=2), encoding='utf-8')
    print(f'Published {len(collected)} episodes to {url}')

if __name__ == '__main__':
    main()
