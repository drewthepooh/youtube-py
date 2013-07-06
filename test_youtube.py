import unittest
from helpers import DateOrderedDict, Video, YouTubeAPIError
from datetime import datetime
import pickle
import youtube
from unittest.mock import patch, MagicMock


class DateOrderedTest(unittest.TestCase):

    videos = {'id1': Video('video1', datetime(2012, 6, 12)),
              'id2': Video('video2', datetime(2012, 6, 11)),
              'id6': Video('video6', datetime(2012, 9, 2)),
              'id3': Video('video3', datetime(2012, 6, 13)),
              'id4': Video('video4', datetime(2012, 2, 28)),
              'id5': Video('video5', datetime(2012, 8, 1))
    }

    more_videos = {'id1': Video('video1', datetime(2013, 6, 12)),
              'id2': Video('video2', datetime(2012, 6, 11)),
    }


    def test_init(self):
        do = DateOrderedDict(self.videos, maxitems=3)
        self.assertTrue(len(do) == 3)
        dates = [video.published for video in do.values()]
        self.assertTrue(datetime(2012, 9, 2) in dates and
                        datetime(2012, 8, 1) in dates and
                        datetime(2012, 6, 13) in dates)

    def test_update(self):
        do = DateOrderedDict(self.videos, maxitems=3)
        do.update(self.more_videos)
        self.assertTrue(len(do) == 3)
        dates = [video.published for video in do.values()]
        self.assertTrue(datetime(2012, 9, 2) in dates and
                        datetime(2012, 8, 1) in dates and
                        datetime(2013, 6, 12) in dates)

class TuberTest(unittest.TestCase):

    def test_handle_API_errors(self):
        t = youtube.Tuber(None, None)
        with open('errors_sample.xml') as xml:
            mock_urlresponse = MagicMock()
            mock_urlresponse.read = xml.read
            mock_urlresponse.status = 400
            mock_urlopen = MagicMock(return_value=mock_urlresponse)
            with patch('youtube.urllib.request.urlopen', new=mock_urlopen):
                self.assertRaisesRegex(YouTubeAPIError,
                                       'too_many_recent_calls',
                                       t.fetch_link, 30)

if __name__ == '__main__':
    unittest.main()

