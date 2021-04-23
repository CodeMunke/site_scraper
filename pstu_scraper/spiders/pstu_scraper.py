from scrapy.spiders import CrawlSpider, Rule, Spider
from scrapy.linkextractors import LinkExtractor
from scrapy import signals

from bs4 import BeautifulSoup
from requests import get
import re
from rutermextract import TermExtractor

from pydispatch import dispatcher

import json
import os

# from scrapy.utils.project import get_project_settings

# settings = get_project_settings()

# settings['FEED_FORMAT'] = 'json'
# settings['FEED_URI'] = 'result.json'

data = []
term_extractor = TermExtractor()

class MySpider(CrawlSpider):
    # def __init__(self):
    #     super()
    #     dispatcher.connect(self.spider_closed, signals.spider_closed)

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
        # dom = BeautifulSoup(get(item['url']).content)
        dom = BeautifulSoup(response.body)
        try:
            item['title'] = response.xpath("//html/head").css("title::text").get()
        except:
            self.log(f"-----------Page skipped: NOT A PAGE-----------")
            return
        # self.log("test1")

        
        try:
            tt = dom.find('div', 'content').text
        except:
            self.log(f"-----------Page skipped: \"{item['title']}\"-----------")
            return            

        # self.log("test2")

        # Убираем знаки все кроме пробелов и кириллицы
        temp_text = "".join(re.findall(r'[а-яА-Я]|\s', tt))
        # Меняем перенос строки и служебный пробел на пробел
        temp_text = temp_text.replace('\n', ' ').replace('\xa0', ' ')
        # Убираем повторяющиеся вхождения пробелов, затем убираем \r и табуляции
        text = (re.sub(r' {2,}', ' ', re.sub(r'(?<! )1(?=[^ ]|$)', '', temp_text))).replace('\r', '').replace('\t', '')

        item['text'] = text
        
        if (not item['text']):
            return

        terms = {}
        for term in term_extractor(text):
            terms[term.normalized] = term.count
        
        item['terms'] = terms

        data.append(item)
        
        self.log(f"----------Scraped page: \"{item['title']}\"-----------")

        # if (not os.path.isfile("./pstu_dump.json")):
        #     with(open("./pstu_dump.json", "w", encoding='utf-8')) as file:
        #         file.write("[\n")
        # else:
        #     with open("data_file.json", "a", encoding='utf-8') as filee:
        #         # filee.write('[')
        #         json.dump({
        #             'url': item['url'],
        #             'title': item['title'],
        #             'text': item['text']
        #         }, filee, ensure_ascii=0, indent=4) 
        #         filee.write(",\n")
            # if index < len(response.css('div.quote')) - 1:
                # filee.write(',')
            # filee.write(']')



        # json.dump(item, open("./pstu_dump.json", "a", encoding="utf-8"), indent=4, ensure_ascii=0)
        # with(open("./pstu_dump.json", "a", encoding='utf-8')) as file:
        #     file.write(",\n")

        # yield {
        #     'url': item['url'],
        #     'title': item['title'],
        #     'text': item['text'],
        # }

    def spider_closed(self, spider, reason):
        self.log("!!!!!!!!!!!!!!!!!SPIDER CLOSED!!!!!!!!!!!!!!!!!!!!!!")
        json.dump(data, open("./pstu_dump.json", "w", encoding="utf-8"), indent=4, ensure_ascii=0)
        # with(open("./pstu_dump.json", "w", encoding="utf-8")) as file:    
            
            # file.write(json.dumps(data))
    
    # def engine_stopped(self, )
        # with(open("./pstu_dump.json", "a", encoding='utf-8')) as file:
        #     file.write("\n]")