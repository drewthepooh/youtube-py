from helpers import *  # Get rid of this
from pprint import pprint
from datetime import datetime
import sys
from bs4 import BeautifulSoup
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
import json, pickle
import urllib.request


class Tuber:
    def __init__(self, username, cached_videos, max_videos=50):
        self.username = username
        self.max_videos = max_videos
        if cached_videos is None:
            cached_videos = DateOrderedDict(maxitems=max_videos)
        self.cache = cached_videos
        self.link = ('https://gdata.youtube.com/feeds/api/users/{username}/uploads?'
                     'max-results={max}'.format(username=self.username, max=self.max_videos))

    def __repr__(self):
        return 'Tuber({!r})'.format(self.username)

    def fetch_link(self, timeout):
        r = urllib.request.urlopen(self.link, timeout=timeout)
        soup = r.read()
        if soup.find('errors'):
            raise YouTubeAPIError(str(soup.errors.code.string))
        return soup

    def get_videos(self):
        '''Returns videos given an xml page from google's youtube API.
        Videos consist of the entry title,
        and a datetime object representing the published date.
        '''
        videos = {}
        soup = self.xmlsoup
        entries = soup.find_all('entry')
        date_pattern = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
        for e in entries:
            ID, title = str(e.find('id').string), str(e.find('media:title').string)
            xml_published = str(e.find('published').string)
            date_match = date_pattern.match(xml_published)
            date = datetime(*(int(x) for x in date_match.groups()))
            videos[ID] = Video(title, date)
        return videos

    def update_cache(self):
        videos = self.get_videos()
        not_seen = videos.keys() - self.cache.keys()
        new = sorted((video for ID, video in videos.items() if ID in not_seen),
                     key=lambda v: v.published, reverse=True)
        old = sorted((video for ID, video in self.cache.items()),
                     key=lambda v: v.published, reverse=True)
        self.cache.update(videos)
        return new, old

    def get_output(self):
        new, old = self.update_cache()
        newheader = colorize('NEW VIDEOS', colors.HEADER)
        oldheader = colorize('OLD VIDEOS', colors.HEADER)
        newout = colorize(wrapp(new), colors.OKBLUE)
        oldout = colorize(wrapp(old[:10]), colors.FAIL)  # A maximum of 10 old videos
        output = '''
{username} videos:
{dash}
NEW VIDEOS:
----------
{new_vids}

PREVIOUSLY CHECKED:
------------------
{old_vids}
'''.format(username=self.username, new_vids=newout, old_vids=oldout,
           dash='='* len(self.username + ' videos'))
        return output


def get_xml(tubers, workers, timeout):
    '''Load in the xml attribute for each tuber.
    No more requests need be made after this'''
    with ThreadPoolExecutor(max_workers=workers) as executor:
        print('Retrieving uploads...', file=sys.stderr)
        future_to_tuber = {executor.submit(t.fetch_link, timeout): t for t in tubers}
        for f in as_completed(future_to_tuber):
            tuber = future_to_tuber[f]
            try:
                tuber.xmlsoup = f.result()
            except Exception as e:
                print('{} generated an exception: {}'.format(tuber, e), file=sys.stderr)
                raise


def _fake_get_xml(tubers):
    '''Purely for testing'''
    with open('jsmith.xml') as jxml, open('ohm_xml.xml') as oxml:
        tubers[0].xml = oxml.read()
        tubers[1].xml = jxml.read()


def export_caches(tubers):
    new_cache = {t.username: t.cache for t in tubers}
    with open('cache.p', 'wb') as pf:
        pickle.dump(new_cache, pf)


def main(max_videos=50):
    # Load in json formatted list of youtube usernames
    with open('tubers.json') as j:
        usernames = json.load(j)

    # Load in the caches
    try:
        with open('cache.p', 'rb') as p:
            caches = pickle.load(p)
    except (FileNotFoundError, EOFError):
        caches = {}

    # Instantiate tubers with cache (or empty cache if not present)
    tubers = []
    for username in usernames:
        cache = caches.get(username, None)
        tubers.append(Tuber(username, cache, max_videos=max_videos))

    # Call get_xml to set xml attributes concurrently
    threads = len(tubers) if len(tubers) <= 20 else 20
    get_xml(tubers, workers=threads, timeout=30)
    # _fake_get_xml(tubers)

    # Get output from each tuber
    output = [t.get_output() for t in tubers]
    print(*output, sep='\n')

    # Update caches for next time
    export_caches(tubers)

if __name__ == '__main__':
    main()


