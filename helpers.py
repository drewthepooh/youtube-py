from collections import OrderedDict, namedtuple
import operator
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


def outer_wrap():
    'closure function so wrapp can use the same textwrapper instance'
    columns = shutil.get_terminal_size().columns
    titles_width = int(columns*0.6)
    date_width = columns - titles_width - 10
    wrapper = textwrap.TextWrapper(subsequent_indent=' '*9,
                                   width=titles_width,
                                   expand_tabs=True)
    def wrapp(videos):
        'helper function which formats videos correctly for output'
        entries = []
        for video in videos:
            title = video.title
            date = 'date: ' + video.published.strftime('%a, %d %b')
            lines = wrapper.wrap(video.title)
            lines[0] = '{:<{}} {:.>{}}   '.format(lines[0],
                                                 titles_width,
                                                 date,
                                                 date_width)
            string = '\n'.join(lines)
            string = textwrap.indent(string, ' --> ',
                                     lambda line: not line.startswith(' '*9))
            entries.append(string)

        return '\n'.join(entries)

    return wrapp

wrapp = outer_wrap()
