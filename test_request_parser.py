#!/usr/bin/env python3

import unittest
import snippets

class TestRequestStringParser(unittest.TestCase):
  known_results = (
    ("", {}),
    ("pickle=", {}),
    ("=====", {}),
    ("snippet_name=", {'snippet_name': ''}),
    ("snippet_name=4348&locale=en-US", {'snippet_name':'4348','locale':'en-US'}),
    ("snippet_name=4348&locale=en-US&", {'snippet_name':'4348','locale':'en-US'}),
    ("snippet_name=4348&locale=en-US&&&&", {'snippet_name':'4348','locale':'en-US'}),
    ("snippet_name=8457&snippet_full_name=MOCO_global_2018_mobile_Focus%20for%20Facebook%20June%20V1_activity%20stream_EN_REL&locale=en-US&country=cz&metric=impression&campaign=FocusforFacebookJune", {'snippet_name':'8457','locale':'en-US','country':'cz','metric':'impression','campaign':'FocusforFacebookJune'}),
    ("snippet_name=8460&snippet_full_name=MOCO_global_2018_utility_Mozilla%20Hubs%20Intro%20V2_activity%20stream_EN_REL&locale=en-US&country=mx&metric=click&campaign=MozillaHubsIntro&href=https%3A//blog.mozvr.com/introducing-hubs-a-new-way-to-get-together-online/%3Fsample_rate%3D0.001%26snippet_name%3D8460%23utm_source%3Ddesktop-snippet%26utm_medium%3Dsnippet%26utm_campaign%3DMozillaHubsIntro%26utm_term%3D8460%26utm_content%3DREL", {'snippet_name':'8460','locale':'en-US','country':'mx','metric':'click','campaign':'MozillaHubsIntro'}),
    ("snippet_name=8460&locale=en-US&country=mx&metric=click&campaign=MozillaHubsIntro&snippet_name=8461", {'snippet_name':'8461','locale':'en-US','country':'mx','metric':'click','campaign':'MozillaHubsIntro'}),
  )

  def test_known_results(self):
    for rs, expected_result in self.known_results:
      actual_result = snippets.parse_request_string(rs)
      self.assertEqual(actual_result, expected_result)

if __name__ == '__main__':
  unittest.main()
