from datetime import datetime
import sys
from bs4 import BeautifulSoup
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
import json, pickle
from collections import OrderedDict
import argparse
import helpers
import logging
import os.path
from textwrap import dedent


class Tuber:

    output_template = dedent('''
    {userhead}:
    {dash}
    {new_head}:
    ------------
    {new_vids}

    {previous_head}:
    --------------------
    {old_vids}
    ''')

    def __init__(self, username, cached_videos, max_videos=50):
        self.username = username
        self.max_videos = max_videos
        if cached_videos is None:
            cached_videos = OrderedDict()
        self.cache = cached_videos
        self.link = ('https://gdata.youtube.com/feeds/api/users/{username}/uploads?'
                     'max-results={max}'.format(username=self.username, max=self.max_videos))

    def __repr__(self):
        return 'Tuber({!r})'.format(self.username)

    def fetch_link(self, timeout=30):
        logging.debug('fetching link for: ' + self.username)
        r = urllib.request.urlopen(self.link, timeout=timeout)
        xml = r.read()
        if r.status != 200:
            soup = BeautifulSoup(xml)
            raise helpers.YouTubeAPIError(soup.errors.code.text)
        logging.debug('finished: ' + self.username)
        return xml

    def get_videos(self):
        '''Returns videos given an xml page from google's youtube API.
        Videos consist of the entry title,
        and a datetime object representing the published date.
        '''
        videos = OrderedDict()  # Videos will be ordered from more recent to less recent
        soup = BeautifulSoup(self.fetch_link())
        entries = soup.find_all('entry')
        date_pattern = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
        for e in entries:
            ID, title = e.find('id').text, e.find('media:title').text
            xml_published = e.find('published').text
            date_match = date_pattern.match(xml_published)
            date = datetime(*(int(x) for x in date_match.groups()))
            videos[ID] = helpers.Video(title, date)
        return videos

    def update_cache(self):
        videos = self.get_videos()  # Ordered dictionary of videos by date
        not_seen = videos.keys() - self.cache.keys()
        new = [video for ID, video in videos.items() if ID in not_seen]
        old = [video for ID, video in self.cache.items()]
        self.cache = videos  # Update the cache
        return new, old

    def get_output(self, max_new, max_old):
        new, old = self.update_cache()
        head = helpers.colorize(self.username.upper() + ' VIDEOS',
                                helpers.colors.HEADER)

        newout = helpers.wrapp(new[:max_new]) if len(new) != 0 else 'No new videos'
        notdisplayed = len(new) - max_new
        if notdisplayed > 0:
            newout += '\n\n... {} additional new videos hidden'.format(notdisplayed)
        newout_col = helpers.colorize(newout, helpers.colors.OKBLUE)

        oldout = helpers.wrapp(old[:max_old]) if len(old) != 0 else 'No previous videos'
        oldout_col = helpers.colorize(oldout, helpers.colors.FAIL)

        output = self.output_template.format(userhead=head,
                                             dash='='* len(head),
                                             new_head='NEW VIDEOS',
                                             previous_head='PREVIOUSLY CHECKED',
                                             new_vids=newout_col,
                                             old_vids=oldout_col)
        return output


def export_caches(tubers, directory):
    caches = {t.username: t.cache for t in tubers}
    with open(os.path.join(directory, 'cache.p'), 'wb') as pf:
        pickle.dump(caches, pf)


def main(max_new, max_old, logger, max_videos=50):
    if logger:
        logging.basicConfig(level=logging.DEBUG)

    directory = os.path.dirname(__file__)

    # Load in json formatted list of youtube usernames
    with open(os.path.join(directory, 'tubers.json')) as j:
        usernames = json.load(j)

    # Load in the caches
    try:
        with open(os.path.join(directory, 'cache.p'), 'rb') as p:
            caches = pickle.load(p)
    except (FileNotFoundError, EOFError):
        caches = {}

    # Instantiate tubers with cache (or empty cache if not present)
    tubers = []
    for username in usernames:
        cache = caches.get(username, None)
        tubers.append(Tuber(username, cache, max_videos=max_videos))

    # Get output concurrently
    with ThreadPoolExecutor(max_workers=20) as executor:
        print('Retrieving uploads...', file=sys.stderr)
        futures = [executor.submit(t.get_output, max_new, max_old) for t in tubers]
        output = [f.result() for f in as_completed(futures)]

    # Print output
    print(*output, sep='\n')

    # Update caches for next time
    export_caches(tubers, directory=directory)

if __name__ == '__main__':
    desc = '''Fetches uploaded videos from youtube users
    specified in tubers.json. Displays new and previously checked videos.
    Will retrieve a maximum of 50 videos.'''
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-n', '--max_new',
                        type=int,
                        default=50,
                        dest='max_new',
                        metavar='num_videos',
                        help='maximum new videos to display')
    parser.add_argument('-o',
                        '--max_old',
                        type=int,
                        default=5,
                        dest='max_old',
                        metavar='num_videos',
                        help='maximum previously checked videos to display')
    parser.add_argument('--debug',
                        action='store_true',
                        dest='logger',
                        help='turn on debugging information')
    args = parser.parse_args()
    main(args.max_new, args.max_old, args.logger)


