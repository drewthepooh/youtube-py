from collections import OrderedDict, namedtuple
import operator
import datetime
import textwrap
import shutil

class YouTubeAPIError(Exception):
    pass

Video = namedtuple('Video', ['title', 'published'])

class DateOrderedDict(OrderedDict):

    def __init__(self, data=None, maxitems=None):
        self.maxitems = maxitems
        super().__init__()
        if data is not None:
            self.update(data)

    def check_items(self):
        if self.maxitems is not None:
            if len(self) > self.maxitems:
                items_by_date = sorted(self.items(),
                                       key=lambda item: item[1].published,
                                       reverse=True)
                while len(self) > self.maxitems:
                    self.pop(items_by_date.pop()[0])

    def update(self, new):
        super().update(new)
        self.check_items()


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
