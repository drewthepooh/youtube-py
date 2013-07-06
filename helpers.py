from collections import namedtuple
import datetime
import textwrap
import shutil

class YouTubeAPIError(Exception):
    pass

Video = namedtuple('Video', ['title', 'published'])

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''

colors = Colors()

def colorize(text, color):
    'helper function with outputs colored strings'
    return color + text + colors.ENDC

def display_date(d):
    now = datetime.datetime.now()
    if d.day == now.day:
        datestring = '      Today'
    elif d.day == now.day - 1:
        datestring = '  Yesterday'
    else:
        datestring = d.strftime('%a, %d %b')
    return datestring


def outer_wrap():
    'Forms a closure allowing wrapp to use a single textwrap instance.'
    columns = shutil.get_terminal_size().columns
    titles_width = int(columns*0.6)
    date_width = columns - titles_width - 10
    sub_indent = ' '*9
    wrapper = textwrap.TextWrapper(subsequent_indent=sub_indent,
                                   width=titles_width,
                                   expand_tabs=True)
    def wrapp(videos):
        'Formats videos for output.'
        entries = []
        for video in videos:
            title = video.title
            date = display_date(video.published)
            lines = wrapper.wrap(video.title)
            lines[0] = '{:<{}} {:.>{}}   '.format(lines[0],
                                                 titles_width,
                                                 date,
                                                 date_width)
            string = '\n'.join(lines)
            string = textwrap.indent(string, ' --> ',
                                     lambda line: not line.startswith(sub_indent))
            entries.append(string)

        return '\n'.join(entries)

    return wrapp

wrapp = outer_wrap()

def _fake_get_xml(tubers):
    '''Purely for testing. Will remove later'''
    with open('jsmith.xml') as jxml, open('ohm_xml.xml') as oxml:
        tubers[0].xml = oxml.read()
        tubers[1].xml = jxml.read()
