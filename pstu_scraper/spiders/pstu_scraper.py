from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy import signals

from bs4 import BeautifulSoup
import re
from rutermextract import TermExtractor

import json

data = []
term_extractor = TermExtractor()

class MySpider(CrawlSpider):
    name = 'texts'
    start_urls = ['https://pstu.ru']


    rules = (
        Rule(LinkExtractor(allow_domains="pstu.ru", deny=[r"\w.pstu.ru"]), callback='parse_item', follow=True),
    )

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(MySpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def parse_item(self, response):
        item = dict()
        item['url'] = response.url
        dom = BeautifulSoup(response.body)
        try:
            item['title'] = response.xpath("//html/head").css("title::text").get()
        except:
            self.log(f"-----------Page skipped: NOT A PAGE-----------")
            return
        
        try:
            tt = dom.find('div', 'content').text
        except:
            self.log(f"-----------Page skipped: \"{item['title']}\"-----------")
            return            

        temp_text = (re.sub(r'\(\d+\.\d+\.\d+\)', '', tt)).replace('\xa0', ' ').replace('\r', ' ') \
            .replace('\n', ' ').replace('\t', ' ')
        text = (re.sub(r' {2,}', ' ', re.sub(r'(?<! )1(?=[^ ]|$)', '', temp_text)))

        item['text'] = text
        
        if not item['text']:
            return

        terms = {}
        for term in term_extractor(text):
            terms[term.normalized] = term.count
        
        item['terms'] = terms

        data.append(item)
        
        self.log(f"----------Scraped page: \"{item['title']}\"-----------")

    def spider_closed(self, spider, reason):
        self.log("!!!!!!!!!!!!!!!!!SPIDER CLOSED!!!!!!!!!!!!!!!!!!!!!!")
        json.dump(data, open("./pstu_dump.json", "w", encoding="utf-8"), indent=4, ensure_ascii=False)
