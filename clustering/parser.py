# from sentence_transformers import SentenceTransformer, util
# import numpy as np
# from datetime import datetime
import random
import re
import time

from bs4 import BeautifulSoup
import cloudscraper
import requests
from tqdm import tqdm  # Для прогрес-бару при парсингу


class ArticleParser:
    def __init__(self, url, title, date, img_url, source):
        self.url = url
        self.title = title
        self.date = date
        self.img_url = img_url
        self.source = source

    def __str__(self):
        return f"{self.title}"

    def __repr__(self):
        return self.__str__()


class Parsing:

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"}

    def __init__(self):
        self.news = []

    def unian(self):
        url = 'https://www.unian.ua/detail/all_news'
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")

        for x in tqdm(soup.findAll('div', class_='list-thumbs__item'), desc='Parsing all unian'):
            # page1 = requests.get(x.find('a', class_='list-thumbs__image')['href'])
            # soup2 = BeautifulSoup(page1.text, "html.parser")

            try:
                self.news.append(ArticleParser(
                    x.find('a', class_='list-thumbs__image')['href'],
                    x.find('a', class_='list-thumbs__title').text.strip(),
                    x.find('div', class_='list-thumbs__time time').text.strip(),
                    x.find('img')['data-src'].replace('thumb_files/220_140_', ''),
                    'unian'
                ))
            except Exception as ex:
                print(f'UNIAN ERROR - {ex}')

            # try:
            #     for j in soup2.find('div', class_='article').findAll('a', class_='article__tag'):
            #         a.tags.append(j.text)
            # except Exception as e:
            #     print(e)
            #
            # self.news.append(a)

    def tsn(self, page_tsn=1):
        url = f'https://tsn.ua/news/page-{page_tsn}'

        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")

        for x in tqdm(soup.find('ul', class_="l-entries l-entries--bordered").findAll('li', class_='l-entries__item'), desc=f'Parsing all tsn page-{page_tsn}'):
            try:
                self.news.append(ArticleParser(
                    x.find('a', class_='c-entry__link u-link-overlay')['href'],
                    x.find('a', class_='c-entry__link u-link-overlay').text.strip(),
                    x.find('time', class_='text-current c-bar__link c-entry__time').text.strip(),
                    x.find('source')['srcset'],
                    'tsn'
                ))
            except Exception as ex:
                print(f'TSN ERROR - {ex}')

    def euro_true(self):
        url = 'https://www.eurointegration.com.ua/news/'
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")

        allNews = soup.findAll('div', class_='article__title')

        [self.news.append(x.text.strip()) for x in
         tqdm(soup.findAll('div', class_='article__title'), desc=f'Parsing all euro_true')]

    def uazmi(self):
        url = 'https://uazmi.org/news'
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")

        [self.news.append(x.text.strip()) for x in
         tqdm(soup.findAll('h3', class_='entry-title'), desc=f'Parsing all uazmi')]

    def radio_svoboda(self):
        url = 'https://www.radiosvoboda.org/z/630'
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")

        x = soup.find('li', class_='col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xs-vertical')

        try:
            self.news.append(ArticleParser(
                url=x.find('a', class_='img-wrap img-wrap--t-spac img-wrap--size-2 img-wrap--float')['href'],
                title=x.find('h4', class_='media-block__title media-block__title--size-2').text.strip(),
                date=x.find('span', class_='date date--mb date--size-2').text.strip(),
                img_url=x.find('div', class_='thumb thumb16_9').find('img')['src'].replace('w100', 'w1023'),
                source='radio_svoboda'
            ))
        except Exception as ex:
            print(f'RADIO_SVOBODA ERROR - {ex}')

        for x in tqdm(soup.findAll('li', class_='col-xs-12 col-sm-12 col-md-12 col-lg-12 fui-grid__inner'), desc='Parsing all radio_svoboda'):
            # print(x)
            try:
                self.news.append(ArticleParser(
                    url=x.find('a', class_='img-wrap img-wrap--t-spac img-wrap--size-3 img-wrap--float img-wrap--xs')['href'],
                    title=x.find('h4', class_='media-block__title media-block__title--size-3').text.strip(),
                    date=x.find('span', class_='date date--mb date--size-3').text.strip(),
                    img_url=x.find('div', class_='thumb thumb16_9').find('img')['src'].replace('w100', 'w1023'),
                    source='radio_svoboda'
                ))
            except Exception as ex:
                print(f'RADIO_SVOBODA ERROR - {ex}')


    def interfax(self):
        scraper = cloudscraper.create_scraper()
        url = 'https://interfax.com.ua/news/latest.html'

        # Отримання сторінки
        page = scraper.get(url)
        soup = BeautifulSoup(page.text, "html.parser")

        for x in tqdm(soup.findAll('div', class_='grid article'), desc='Parsing all interfax'):
            # print(x)
            try:
                self.news.append(ArticleParser(
                    url=f'https://interfax.com.ua/{x.find('a', class_='article-link')['href']}',
                    title=x.find('a', class_='article-link').text.strip(),
                    date=f'{x.find('div', class_='col-13 article-time').findAll('span')[0].text}, {x.find('div', class_='col-13 article-time').findAll('span')[1].text}',
                    img_url=x.find('div', class_='col-23').find('img', class_='article-image')['src'],
                    source='interfax'
                ))
            except Exception as ex:
                print(f'INTERFAX ERROR - {ex}')

    def ukrinform(self):
        scraper = cloudscraper.create_scraper()
        url = 'https://www.ukrinform.ua/block-lastnews'

        # Отримання сторінки
        page = scraper.get(url)
        soup = BeautifulSoup(page.text, "html.parser")

        for x in tqdm(soup.find('section', class_="restList").findAll('article'), desc=f'Parsing all ukrinform'):
            try:
                self.news.append(ArticleParser(
                    url=f"https://www.ukrinform.ua/{x.find('a')['href']}",
                    title=x.find('img')['alt'],
                    date=x.find('time')['datetime'],
                    img_url=x.find('img')['src'].strip().replace('360_240', '630_360'),
                    source='ukrinform'
                ))
            except Exception as ex:
                print(f'UKR_INFORM ERROR - {ex}')

    def glavcom(self):
        scraper = cloudscraper.create_scraper()
        url = 'https://glavcom.ua/news.html'

        # Отримання сторінки
        page = scraper.get(url)
        soup = BeautifulSoup(page.text, "html.parser")

        [self.news.append(x.text.strip()) for x in
         tqdm(soup.findAll('div', class_='article_title'),desc=f'Parsing all glavcom')]

    def znua(self):
        scraper = cloudscraper.create_scraper()

        url = 'https://zn.ua/ukr/all-news'

        # Отримання сторінки
        page = scraper.get(url)
        soup = BeautifulSoup(page.text, "html.parser")

        [self.news.append(x.text.strip()) for x in
         tqdm(soup.findAll('a', class_='content-news__link sunsite_action'),desc=f'Parsing all znua')]

    def rbk_ukr(self):
        pass

    def show_news(self):
        for data in self.news:
            print(data)
            # print(f"{data['title']}")
            # print(f"Дата: {data['date']}")
            # print("Текст статті:")
            # print(data['article_text'])
            # print("---\n")

    def return_news(self):
        self.unian(), self.tsn(), self.uazmi(), self.radio_svoboda(), self.interfax(), self.glavcom(), self.znua()
        return self.news

# 'https://news.liga.net/ua'


# Завантаження моделі для класифікації тексту
# classifier = pipeline("zero-shot-classification",
#                       model="facebook/bart-large-mnli")

# classifier = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")

# model_name = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
#

# categories = {
#     "Політика": [
#         "Внутрішня політика",
#         "Міжнародна політика",
#         "Законодавство",
#         "Політичні партії",
#         "Вибори"
#     ],
#     "Економіка та бізнес": [
#         "Фінанси",
#         "Бізнес-новини",
#         "Ринок праці",
#         "Підприємництво",
#         "Торгові угоди"
#     ],
#     "Технології та наука": [
#         "Інформаційні технології",
#         "Наукові дослідження",
#         "Інновації",
#         "Космос",
#         "Медицина"
#     ],
#     "Світ": [
#         "Міжнародні події",
#         "Геополітика",
#         "Конфлікти",
#         "Міжнародні організації",
#         "Дипломатія"
#     ],
#     "Україна": [
#         "Внутрішні події",
#         "Регіональні новини",
#         "Міста України",
#         "Суспільні ініціативи",
#         "Освіта в Україні"
#     ],
#     "Війна": [
#         "Бойові дії",
#         "Стратегія та тактика",
#         "Збройні сили",
#         "Конфлікти",
#         "Оборонні технології"
#     ],
#     "Спорт": [
#         "Футбол",
#         "Баскетбол",
#         "Теніс",
#         "Олімпійські ігри",
#         "Інші види спорту"
#     ],
#     "Здоров'я та медицина": [
#         "Медицина",
#         "Здоровий спосіб життя",
#         "Хвороби",
#         "Фармацевтика",
#         "Психологія"
#     ],
#     "Культура та мистецтво": [
#         "Мистецтво",
#         "Література",
#         "Музика",
#         "Кіно та театр",
#         "Виставки та фестивалі"
#     ],
#     "Шоу-бізнес / Розваги": [
#         "Кінематограф",
#         "Телебачення",
#         "Музиканти та актори",
#         "Світські події",
#         "Паліативні події"
#     ],
#     "Подорожі / Туризм": [
#         "Туристичні напрямки",
#         "Транспорт",
#         "Готелі та проживання",
#         "Автомобілі",
#         "Кулінарні подорожі"
#     ],
#     "Освіта та соціальні питання": [
#         "Освіта та навчання",
#         "Пенсії та соціальні виплати",
#         "Волонтерство та благодійність",
#         "Кримінал та правопорушення",
#         "Суспільні події та ініціативи",
#         "Демографія та міграція"
#     ],
#     "Ігри та кіберспорт": [
#         "Відеоігри",
#         "Кіберспорт",
#         "Розробка ігор",
#         "Ігрова індустрія",
#         "VR/AR технології"
#     ],
#     "Екологія": [
#         "Навколишнє середовище",
#         "Кліматичні зміни",
#         "Збереження природи",
#         "Відходи та переробка",
#         "Енергетика"
#     ],
#     "Інше": [
#         "Невизначені теми",
#         "Нестандартні новини",
#         "Технічні помилки",
#         "Інші категорії"
#     ]
# }
#
#
# def classify_news(text):
#     # Крок 1: Визначення головної категорії
#     main_labels = list(categories.keys())
#     main_result = classifier(text, main_labels, multi_label=False)
#     main_category = main_result['labels'][0]
#     main_score = main_result['scores'][0]
#
#     # Крок 2: Визначення підкатегорії
#     sub_labels = categories.get(main_category, [])
#     if sub_labels:
#         sub_result = classifier(text, sub_labels, multi_label=False)
#         sub_category = sub_result['labels'][0]
#         sub_score = sub_result['scores'][0]
#     else:
#         sub_category = "Немає підкатегорії"
#         sub_score = 0.0
#
#     return {
#         "Текст для аналізу": f"\"{text}\"",
#         "Головна категорія": f"{main_category}: {main_score:.2%}",
#         "Підкатегорія": f"{sub_category}: {sub_score:.2%}"
#     }
#
#
# for text in tt.news:
#     # Завантажте NLP-модель для української мови
#     nlp = spacy.load("uk_core_news_sm")
#
#     # Аналіз тексту
#     doc = nlp(text.title)
#
#     # Витяг географічних назв
#     places = [ent.text for ent in doc.ents if ent.label_ == "LOC"]  # GPE: геополітична сутність
#     print(text, '\n', places)
#
#     # Текст для аналізу
#     # candidate_labels = [
#     #     'Україна',
#     #     "Політика",
#     #     "Економіка",
#     #     "Технології",
#     #     "Наука",
#     #     "Світ",
#     #     "Війна",
#     #     "Спорт",
#     #     "Здоров'я",
#     #     "Розваги та культура",
#     #     "Подорожі",
#     #     'Різне',
#     #     "Ігри та кіберспорт"
#     # ]
#
#
#     # candidate_labels = [
#     #     "Політика",
#     #     "Економіка та бізнес",
#     #     "Технології та наука",
#     #     "Світ",
#     #     "Україна",
#     #     "Війна",
#     #     "Спорт",
#     #     "Здоров'я та медицина",
#     #     "Культура та мистецтво",
#     #     "Шоу-бізнес / Розваги",
#     #     "Подорожі / Туризм",
#     #     "Суспільство / Соціальні питання",
#     #     "Ігри та кіберспорт",
#     #     "Екологія",
#     #     "Інше"
#     # ]
#
#     result = classify_news(text.title)
#     print("Текст для аналізу:")
#     print(result["Текст для аналізу"], "\n")
#     print(result["Головна категорія"])
#     print(result["Підкатегорія"], "\n")
#     print("-" * 80)

categories = {
    "Політика": [
        "Внутрішня політика",
        "Міжнародна політика",
        "Законодавство",
        "Політичні партії",
        "Вибори"
    ],
    "Економіка та бізнес": [
        "Фінанси",
        "Бізнес-новини",
        "Ринок праці",
        "Підприємництво",
        "Торгові угоди"
    ],
    "Технології та наука": [
        "Інформаційні технології",
        "Наукові дослідження",
        "Інновації",
        "Космос",
        "Медицина"
    ],
    "Світ": [
        "Міжнародні події",
        "Геополітика",
        "Конфлікти",
        "Міжнародні організації",
        "Дипломатія"
    ],
    "Україна": [
        "Внутрішні події",
        "Регіональні новини",
        "Міста України",
        "Суспільні ініціативи",
        "Освіта в Україні"
    ],
    "Війна": [
        "Бойові дії",
        "Стратегія та тактика",
        "Збройні сили",
        "Конфлікти",
        "Оборонні технології"
    ],
    "Спорт": [
        "Футбол",
        "Баскетбол",
        "Теніс",
        "Олімпійські ігри",
        "Інші види спорту"
    ],
    "Здоров'я та медицина": [
        "Медицина",
        "Здоровий спосіб життя",
        "Хвороби",
        "Фармацевтика",
        "Психологія"
    ],
    "Культура та мистецтво": [
        "Мистецтво",
        "Література",
        "Музика",
        "Кіно та театр",
        "Виставки та фестивалі"
    ],
    "Шоу-бізнес / Розваги": [
        "Кінематограф",
        "Телебачення",
        "Музиканти та актори",
        "Світські події",
        "Паліативні події"
    ],
    "Подорожі / Туризм": [
        "Туристичні напрямки",
        "Транспорт",
        "Готелі та проживання",
        "Автомобілі",
        "Кулінарні подорожі"
    ],
    "Освіта та соціальні питання": [
        "Освіта та навчання",
        "Пенсії та соціальні виплати",
        "Волонтерство та благодійність",
        "Кримінал та правопорушення",
        "Суспільні події та ініціативи",
        "Демографія та міграція"
    ],
    "Ігри та кіберспорт": [
        "Відеоігри",
        "Кіберспорт",
        "Розробка ігор",
        "Ігрова індустрія",
        "VR/AR технології"
    ],
    "Екологія": [
        "Навколишнє середовище",
        "Кліматичні зміни",
        "Збереження природи",
        "Відходи та переробка",
        "Енергетика"
    ],
    "Інше": [
        "Невизначені теми",
        "Нестандартні новини",
        "Технічні помилки",
        "Інші категорії"
    ]
}


def classify_news(text):
    # Крок 1: Визначення головної категорії
    main_labels = list(categories.keys())
    main_result = classifier(text, main_labels, multi_label=False)
    main_category = main_result['labels'][0]
    main_score = main_result['scores'][0]

    # Крок 2: Визначення підкатегорії
    sub_labels = categories.get(main_category, [])
    if sub_labels:
        sub_result = classifier(text, sub_labels, multi_label=False)
        sub_category = sub_result['labels'][0]
        sub_score = sub_result['scores'][0]
    else:
        sub_category = "Немає підкатегорії"
        sub_score = 0.0

    return {
        "Текст для аналізу": f"\"{text}\"",
        "Головна категорія": f"{main_category}: {main_score:.2%}",
        "Підкатегорія": f"{sub_category}: {sub_score:.2%}"
    }

    # Текст для аналізу
    # candidate_labels = [
    #     'Україна',
    #     "Політика",
    #     "Економіка",
    #     "Технології",
    #     "Наука",
    #     "Світ",
    #     "Війна",
    #     "Спорт",
    #     "Здоров'я",
    #     "Розваги та культура",
    #     "Подорожі",
    #     'Різне',
    #     "Ігри та кіберспорт"
    # ]


    # candidate_labels = [
    #     "Політика",
    #     "Економіка та бізнес",
    #     "Технології та наука",
    #     "Світ",
    #     "Україна",
    #     "Війна",
    #     "Спорт",
    #     "Здоров'я та медицина",
    #     "Культура та мистецтво",
    #     "Шоу-бізнес / Розваги",
    #     "Подорожі / Туризм",
    #     "Суспільство / Соціальні питання",
    #     "Ігри та кіберспорт",
    #     "Екологія",

