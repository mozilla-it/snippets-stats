#!/usr/bin/env python3

import unittest
import snippets

class TestLogLineParser(unittest.TestCase):
  known_results = (
    ("", (None, None, None, None)),
    ('1.2.3.4 snippets-stats.mozilla.org - [19/Jun/2018:04:00:22 +0000] "GET /foo.html?snippet_name=7866&snippet_full_name=MOCO_global_2018_f100_week2_campaign_webliteracy_activity_stream_EN_REL&locale=en-US&country=in&metric=impression&campaign=f100%20web%20literacy HTTP/1.1" 200 344 "-" "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0" "-" "cached" "ssl:SSL_ECDHE_RSA_WITH_AES_128_GCM_SHA256, version=TLSv1.2, bits=128" "node:-" node_s:- req_s:0.001354 retries:0 queued:-',
     ('1.2.3.4', '19/Jun/2018:04:00:22 +0000', 'snippet_name=7866&snippet_full_name=MOCO_global_2018_f100_week2_campaign_webliteracy_activity_stream_EN_REL&locale=en-US&country=in&metric=impression&campaign=f100%20web%20literacy', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0')),
    ('1.2.3.4 snippets-stats.mozilla.org - [19/Jun/2018:04:00:22 +0000] "HEAD /foo.html? HTTP/1.1" 200 344 "-" "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0"',
     (None, None, None, None)),
  )

  def test_known_results(self):
    for rs, expected_result in self.known_results:
      actual_result = snippets.extract_fields(rs)
      self.assertEqual(actual_result, expected_result)

if __name__ == '__main__':
  unittest.main()
