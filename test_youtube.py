import unittest
from helpers import TuberCache, Video, YouTubeAPIError
from datetime import datetime
import pickle
import youtube
from unittest.mock import patch, MagicMock


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

