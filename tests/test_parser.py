import unittest

import news_parser

SAMPLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>Sample</title>
<item>
  <title>Hello <b>world</b></title>
  <link>https://example.com/1</link>
  <description>Body <i>text</i></description>
  <pubDate>Mon, 09 Nov 2026 10:00:00 GMT</pubDate>
</item>
<item>
  <title>Duplicate link</title>
  <link>https://example.com/1</link>
  <description>dup</description>
</item>
<item>
  <title>Third item</title>
  <link>https://example.com/2</link>
  <description>other</description>
</item>
</channel></rss>
"""


class ParserTest(unittest.TestCase):
    def test_strip_html(self):
        self.assertEqual(news_parser.strip_html("<p>a <b>b</b></p>"), "a b")
        self.assertEqual(news_parser.strip_html(""), "")

    def test_parse_dedupes_and_strips(self):
        articles = news_parser.parse(SAMPLE, source="sample", limit=10)
        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0].title, "Hello world")
        self.assertEqual(articles[0].summary, "Body text")
        self.assertEqual(articles[0].source, "sample")
        self.assertTrue(articles[0].published.startswith("2026-11-09"))

    def test_parse_limit(self):
        articles = news_parser.parse(SAMPLE, source="sample", limit=1)
        self.assertEqual(len(articles), 1)

    def test_filter_keyword(self):
        articles = news_parser.parse(SAMPLE, source="sample", limit=10)
        self.assertEqual(len(news_parser.filter_keyword(articles, "third")), 1)
        self.assertEqual(len(news_parser.filter_keyword(articles, "nomatch")), 0)


if __name__ == "__main__":
    unittest.main()
