from requests import get
from bs4 import BeautifulSoup
from pymorphy2 import MorphAnalyzer
import re
from rutermextract import TermExtractor
from pprint import pprint
import json

te = TermExtractor()

dialogs = []

n_question = 1
n_prev = 0
try:
    while True:
        address = 'https://pstu.ru/enrollee/feedback/?p={}&search='.format(n_question)
        print("Currently on question #{}".format(n_question))
        print(address)
        html = get(address).content
        dom = BeautifulSoup(html, features='lxml')
        strongs = dom('strong')
        if n_question == n_prev:
            raise Exception("Parsing finished at question {}".format(n_question))
        else:
            n_prev = n_question
        for strong in strongs:
            if strong.text == 'Ответ:':
                try:
                    name = strong.previous_sibling.previous_sibling.previous_sibling.text.replace(':', '')
                    question = strong.previous_sibling.text
                    answer_elm = strong.next_sibling.next_sibling
                    try:
                        href = answer_elm('a')[0]['href']
                    except (IndexError, KeyError):
                        href = ''

                    date = (re.findall(r'\(\d+\.\d+\.\d+\)', question)[0]).replace('(', '').replace(')', '')
                    question = (re.sub(r'\(\d+\.\d+\.\d+\)', '', question)).replace('\xa0', ' ').replace('\r', ' ')\
                        .replace('\n', ' ').replace('\t', ' ')
                    answer = answer_elm.text.replace('\xa0', ' ').replace('\r', ' ').replace('\n', ' ').\
                        replace('\t', ' ')

                    question = (re.sub(r' {2,}', ' ', re.sub(r'(?<! )1(?=[^ ]|$)', '', question)))
                    answer = (re.sub(r' {2,}', ' ', re.sub(r'(?<! )1(?=[^ ]|$)', '', answer)))

                    terms = [str(x) for x in te(answer + ' ' + question) if str(x).count(' ') > 0]

                    n_question += 1

                    assert len(terms) > 0

                    dialogs += [
                        {
                            'name': name,
                            'question': question,
                            'answer': answer,
                            'date': date,
                            'href': href,
                            'terms': terms,
                        }
                    ]
                except AssertionError:
                    pass
        # pprint(dialogs)
        # print('------------------------------------------------------------')
        # open("/pstu_qa_{}".format(n_question), "w", encoding="utf-8").write()
except Exception as e:
    print("\nPARSING STOPPED because of:")
    print(e)
finally:
    json.dump(dialogs, open("../pstu_qa_{}.json".format(n_question), "w", encoding="utf-8"), indent=4,
              ensure_ascii=False)
