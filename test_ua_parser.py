#!/usr/bin/env python3

import unittest
import snippets

class TestUAParser(unittest.TestCase):
  def test_basic_parse_windows(self):
    self.assertEqual(snippets.parse_ua_string("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0"),{'os_family':'Windows 10','ua_family':'Firefox','ua_major':'60'})
    self.assertNotEqual(snippets.parse_ua_string("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0"),{'os_family':'Windows 8','ua_family':'Firefox','ua_major':'60'})

  def test_basic_parse_macos(self):
    self.assertEqual(snippets.parse_ua_string("Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:60.0) Gecko/20100101 Firefox/60.0"),{'os_family':'Mac OS X','ua_family':'Firefox','ua_major':'60'})

  def test_basic_parse_macos_9(self):
    self.assertEqual(snippets.parse_ua_string("Mozilla/5.0 (Macintosh; Intel Mac OS 9; rv:60.0) Gecko/20100101 Firefox/60.0"),{'os_family':'Mac OS 9','ua_family':'Firefox','ua_major':'60'})

  def test_basic_parse_safari(self):
    self.assertEqual(snippets.parse_ua_string("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36"),{'os_family':'Linux','ua_family':'Chrome','ua_major':'36'})

  def test_parse_fail(self):
    self.assertEqual(snippets.parse_ua_string("Mozilla/5.0"),{'os_family':'Other','ua_family':'Other','ua_major':'Other'})

  def test_parse_empty(self):
    self.assertEqual(snippets.parse_ua_string(''),{'os_family':'Other','ua_family':'Other','ua_major':'Other'})

  def test_parse_tricky(self):
    self.assertEqual(snippets.parse_ua_string("Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.8.1.1) Gecko/20061205 Iceweasel/2.0.0.1 (Debian-2.0.0.1+dfsg-4)"),{'os_family':'Linux','ua_family':'Iceweasel','ua_major':'2'})

  def test_parse_tricky_2(self):
    self.assertEqual(snippets.parse_ua_string("Mozilla/5.0 (X11; Linux mips64; rv:17.0) Gecko/20131031 Firefox/17.0 Iceweasel/17.0.10"),{'os_family':'Linux','ua_family':'Firefox','ua_major':'17'})

if __name__ == '__main__':
  unittest.main()
