from datetime import datetime
import sys
from bs4 import BeautifulSoup
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
import json, pickle
import helpers
from collections import OrderedDict

# Add in ability to control output and other options from the commandline
# Add short circuit if xml is not modified. There are no new, don't update cache

class Tuber:

    output_template = '''
{userhead}:
{dash}
{new_head}:
------------
{new_vids}

{previous_head}:
--------------------
{old_vids}
'''

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

    def fetch_link(self, timeout):
        r = urllib.request.urlopen(self.link, timeout=timeout)
        xml = r.read()
        if r.status != 200:
            soup = BeautifulSoup(xml)
            raise helpers.YouTubeAPIError(str(soup.errors.code.string))
        return xml

    def get_videos(self):
        '''Returns videos given an xml page from google's youtube API.
        Videos consist of the entry title,
        and a datetime object representing the published date.
        '''
        videos = OrderedDict()  # Videos will be ordered from more recent to less recent
        soup = BeautifulSoup(self.xml)  # Set by get_xml function
        entries = soup.find_all('entry')
        date_pattern = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
        for e in entries:
            ID, title = str(e.find('id').string), str(e.find('media:title').string)
            xml_published = str(e.find('published').string)
            date_match = date_pattern.match(xml_published)
            date = datetime(*(int(x) for x in date_match.groups()))
            videos[ID] = helpers.Video(title, date)
        return videos

    def update_cache(self):
        videos = self.get_videos()  # Ordered dictionary of videos by date
        not_seen = videos.keys() - self.cache.keys()
        new = [video for ID, video in videos.items() if ID in not_seen]
        old = [video for ID, video in self.cache.items()]
        self.cache = videos  # Update the cache with new videos
        return new, old

    def get_output(self):
        new, old = self.update_cache()
        head = helpers.colorize(self.username.upper() + ' VIDEOS', helpers.colors.HEADER)
        newout = helpers.wrapp(new) if len(new) != 0 else 'No new videos'
        newout_col = helpers.colorize(newout, helpers.colors.OKBLUE)
        oldout = helpers.wrapp(old[:8])  # A maximum of 8 old videos
        oldout_col = helpers.colorize(oldout, helpers.colors.FAIL)
        output = self.output_template.format(userhead=head,
                                             dash='='* len(head),
                                             new_head='NEW VIDEOS',
                                             previous_head='PREVIOUSLY CHECKED',
                                             new_vids=newout_col,
                                             old_vids=oldout_col)
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
                tuber.xml = f.result()
            except Exception as e:
                print('{} generated an exception: {}'.format(tuber, e), file=sys.stderr)
                raise


def export_caches(tubers):
    caches = {t.username: t.cache for t in tubers}
    with open('cache.p', 'wb') as pf:
        pickle.dump(caches, pf)


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
    # helpers._fake_get_xml(tubers)

    # Get output from each tuber
    output = [t.get_output() for t in tubers]
    print(*output, sep='\n')

    # Update caches for next time
    export_caches(tubers)

if __name__ == '__main__':
    main()


