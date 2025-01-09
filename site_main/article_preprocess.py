
from bs4 import BeautifulSoup
import cloudscraper
import markdownify
import requests


def tsn_preprocess(url):
    url = url
    sign = ''

    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")

    title = soup.find('h1', class_='c-card__title').text
    date = soup.find('time').text
    src = soup.find('picture').find('source')['srcset']
    try:
        sign = soup.find('div', class_='c-card__media__caption i-before i-info').text
    except AttributeError:
        pass

    content = soup.new_tag('div', attrs={'class': 'article-content'})
    try:
        lead = soup.new_tag('h2', attrs={
            'class': 'lead-text'})
        lead.string = soup.find('div', class_='c-article__body').find('div', class_='c-article__lead').text
        content.append(lead)
    except Exception as ex:
        print(ex)

    content1 = soup.find('div', class_='c-article__body').findAll('div')[5]
    if content1.text == '':
        content1 = soup.find('div', class_='c-article__body').findAll('div')[6]
    content.append(content1)

    for i in content.findAll('p'):
        i['class'] = 'new-text'
        if i.text.strip() == 'Читайте також:':
            sibling = i.next_sibling
            while sibling:
                next_sibling = sibling.next_sibling
                sibling.extract()
                sibling = next_sibling
            i.decompose()

    for i in content.findAll('h2'):
        try:
            if i['class'][0] == 'lead-text':
                continue
        except:
            i['class'] = 'new-subtitles'
    for i in content.findAll('h3'):
        i['class'] = 'new-subtitles'
        if i.text.strip() == 'Читайте також:':
            sibling = i.next_sibling
            while sibling:
                next_sibling = sibling.next_sibling
                sibling.extract()
                sibling = next_sibling
            i.decompose()

    try:
        aside_node = content.findAll('aside', class_='c-article__note')
        for i in aside_node:
            if i.find('h3', class_='new-subtitles').text == 'Також читайте':
                i.decompose()
    except Exception as e:
        print(e)

    for item, img in zip(content.findAll('div', class_='c-figure c-figure__row'),
                         content.findAll('img', class_='c-card__embed__img')):

        tag = soup.new_tag('div', attrs={'class': 'new-img-sub'})

        new_tag = soup.new_tag('img', attrs={'src': img['data-src'], 'class': 'new-img-sub', 'loading': 'lazy'})
        tag.append(new_tag)
        try:
            sing_tag = soup.new_tag('p', attrs={
                'class': 'img-sign-sub'})
            sing_tag.string = item.find('div', class_='c-card__media__caption i-before i-info').text
            tag.append(sing_tag)
        except AttributeError:
            pass

        item.replace_with(tag)

    if content.findAll('iframe'):
        for item in content.findAll('iframe'):
            tag = soup.new_tag('div', attrs={'class': 'article-iframe-video'})
            video_tag = soup.new_tag('iframe', attrs={'src': item['data-src'], 'styles': 'width: 43vw; height: 24.2vw', 'loading':'lazy', 'allowfullscreen':''})
            tag.append(video_tag)
            item.replace_with(tag)
    try:
        twitter_content = soup.findAll('div', class_='c-figure c-figure__row c-figure__row--sdmd')
        for tweet in twitter_content:
            tweet['class'] = 'new-img-sub'
    except AttributeError:
        pass

    article_data = {
        'title': title,
        'date': date,
        'main_img': {'src': src, 'sign': sign},
        'content': content.prettify()
    }

    return article_data


def unian_preprocess(url):
    url = url
    sign = ''

    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    title = soup.find('h1').text
    date = soup.find('div', class_='article__info-item time').text
    src = soup.find('figure', class_='photo_block').find('img')['data-src']
    try:
        sign = soup.find('figcaption', class_='subscribe_photo_text').text
    except AttributeError:
        pass

    content = soup.new_tag('div', attrs={'class': 'article-content'})
    try:
        lead = soup.new_tag('h2', attrs={
            'class': 'lead-text'})
        lead.string = soup.find('p', class_='article__like-h2').text
        content.append(lead)
    except Exception as ex:
        print(ex)
    content.append(soup.find('div', class_='article-text'))

    for i in content.findAll('p'):
        i['class'] = 'new-text'
        if i.text.strip() == 'Вас також можуть зацікавити новини:':
            sibling = i.next_sibling
            while sibling:
                next_sibling = sibling.next_sibling
                sibling.extract()
                sibling = next_sibling
            i.decompose()

    for i in content.findAll('h2'):
        if i.text == 'Вас також можуть зацікавити новини:':
            sibling = i.next_sibling
            while sibling:
                next_sibling = sibling.next_sibling
                sibling.extract()
                sibling = next_sibling
            i.decompose()
        else:
            try:
                if i['class'][0] == 'lead-text':
                    continue
            except:
                i['class'] = 'new-subtitles'

    try:
        content.find('figure', class_='photo_block').decompose()
        content.find('div', class_='read-also-slider').decompose()
        content.find('div', class_='nts-video-wrapper').decompose()
    except AttributeError:
        try:
            content.find('div', class_='read-also-slider').decompose()
            content.find('div', class_='nts-video-wrapper').decompose()
        except AttributeError:
            try:
                content.find('div', class_='nts-video-wrapper').decompose()
            except AttributeError:
                pass

    for item in content.findAll('figure', class_='photo_block'):

        tag = soup.new_tag('div', attrs={'class': 'new-img-sub'})

        new_tag = soup.new_tag('img', attrs={'src': item.find('img')['data-src'], 'class': 'new-img-sub', 'loading': 'lazy'})
        tag.append(new_tag)
        try:
            sing_tag = soup.new_tag('p', attrs={
                'class': 'img-sign-sub'})
            sing_tag.string = item.find('figcaption', class_='subscribe_photo_text').text
            tag.append(sing_tag)
        except AttributeError:
            pass

        item.replace_with(tag)

    article_data = {
        'title': title,
        'date': date,
        'main_img': {'src': src, 'sign': sign},
        'content': content.prettify()
    }

    return article_data


class ArticlePreprocessor:
    @staticmethod
    def create(source, url):
        if source == 'tsn':
            return tsn_preprocess(url)
        elif source == 'unian':
            return unian_preprocess(url)
        else:
            raise ValueError(f"Unsupported source: {source}")
#
# # unian_preprocess('https://www.unian.ua/war/mozhlive-otochennya-deepstate-diznavsya-pro-situaciyu-bilya-odnogo-z-naselenih-punktiv-donechchini-12852525.html')

# 'instagram-media instagram-media-rendered'

# from bs4 import BeautifulSoup
# import requests
#
#
# class ArticlePreprocessorObject:
#     def __init__(self, url, selectors):
#         self.url = url
#         self.selectors = selectors
#         self.soup = None
#
#     def __call__(self):
#         self.fetch_page()
#         return self.preprocess()
#
#     def fetch_page(self):
#         # Завантажуємо сторінку
#         try:
#             page = requests.get(self.url)
#             page.raise_for_status()
#             self.soup = BeautifulSoup(page.text, "html.parser")
#         except requests.RequestException as e:
#             raise ValueError(f"Failed to fetch page: {e}")
#
#     def preprocess(self):
#         """
#         Загальна функція обробки статей.
#         """
#         try:
#             title = self.extract_text('title')
#             date = self.extract_text('date')
#             img_src = self.extract_attribute('img', 'src', default='')
#             content = self.soup.select_one(self.selectors['content'])
#
#             if not content:
#                 raise AttributeError("Content not found")
#
#             self.clean_content(content)
#
#             return {
#                 'title': title,
#                 'date': date,
#                 'main_img': {'src': img_src, 'sign': self.extract_caption()},
#                 'content': content.prettify()
#             }
#         except Exception as e:
#             return {'error': f'Failed to preprocess article: {e}'}
#
#     def extract_text(self, key):
#         """Витягує текст із вказаного селектора."""
#         try:
#             return self.soup.select_one(self.selectors[key]).text.strip()
#         except AttributeError:
#             return ''
#
#     def extract_attribute(self, key, attribute, default=None):
#         """Витягує атрибут із вказаного селектора."""
#         try:
#             return self.soup.select_one(self.selectors[key])[attribute]
#         except (AttributeError, KeyError, TypeError):
#             return default
#
#     def clean_content(self, content):
#         """Очищення зайвих елементів з контенту."""
#         for unwanted in content.find_all(['aside', 'div', 'figure'], class_=['read-also-slider', 'nts-video-wrapper']):
#             unwanted.decompose()
#
#         for tag in content.find_all(['p', 'h2', 'h3']):
#             tag['class'] = 'new-text' if tag.name == 'p' else 'new-subtitles'
#             if tag.text.strip() in ['Читайте також:', 'Вас також можуть зацікавити новини:']:
#                 self.remove_siblings(tag)
#
#         # Обробка вбудованих Twitter постів
#         for twitter_post in content.find_all('blockquote', class_='twitter-tweet'):
#             twitter_div = self.soup.new_tag('div', attrs={'class': 'embedded-twitter'})
#             twitter_div.append(twitter_post)
#             twitter_post.replace_with(twitter_div)
#
#         # Обробка вбудованих Instagram постів
#         for instagram_post in content.find_all('blockquote', class_='instagram-media'):
#             instagram_div = self.soup.new_tag('div', attrs={'class': 'embedded-instagram'})
#             instagram_div.append(instagram_post)
#             instagram_post.replace_with(instagram_div)
#
#     def remove_siblings(self, tag):
#         """Видаляє сусідні елементи після заданого тегу."""
#         sibling = tag.next_sibling
#         while sibling:
#             next_sibling = sibling.next_sibling
#             sibling.extract()
#             sibling = next_sibling
#         tag.decompose()
#
#     def extract_caption(self):
#         """Витягує підпис до зображення, якщо є."""
#         try:
#             caption = self.soup.select_one(self.selectors.get('caption', '')).text.strip()
#         except AttributeError:
#             caption = ''
#         return caption
#
#
# class ArticlePreprocessor:
#     @staticmethod
#     def create(source, url):
#         if source == 'tsn':
#             return TSNPreprocessor(url)()
#         elif source == 'unian':
#             return UnianPreprocessor(url)()
#         else:
#             raise ValueError(f"Unsupported source: {source}")
#
#
# class TSNPreprocessor(ArticlePreprocessorObject):
#     def __init__(self, url):
#         selectors = {
#             'title': 'h1.c-card__title',
#             'date': 'time',
#             'img': 'picture source[srcset]',
#             'content': 'div.c-article__body',
#             'caption': 'div.c-card__media__caption.i-before.i-info'
#         }
#         super().__init__(url, selectors)
#

# class UnianPreprocessor(ArticlePreprocessorObject):
#     def __init__(self, url):
#         selectors = {
#             'title': 'h1',
#             'date': 'div.article__info-item.time',
#             'img': 'figure.photo_block img[data-src]',
#             'content': 'div.article-text',
#             'caption': 'figcaption.subscribe_photo_text'
#         }
#         super().__init__(url, selectors)
#
# # Приклад використання
# # tsn_processor = TSNPreprocessorObject('https://example.com/tsn_article')
# # tsn_data = tsn_processor()
#
# # unian_processor = UnianPreprocessorObject('https://example.com/unian_article')
# # unian_data = unian_processor()
