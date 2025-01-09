import time
import uuid

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from clustering.models import Article, Cluster
from site_main.article_preprocess import ArticlePreprocessor
from django.core.cache import cache
from clustering.utils import set_cache_cluster


def index(request):
    cache_key = f"clusters_data"
    if request.session.get(f'filter_source') is None:
        request.session[f'filter_source'] = 0

    filter_source = request.session.get(f'filter_source')
    sources = request.session.get('filterSources')

    if filter_source != 0:
        clusters_data = []
        for source in sources:
            clusters_data += cache.get(f"clusters_data_{source}")
    else:
        clusters_data = cache.get(cache_key)

    if not clusters_data:
        set_cache_cluster()

    page_number = int(request.GET.get("page", 1))

    paginator = Paginator(clusters_data, 20, orphans=1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'index1.html', {'clusters': page_obj, 'filter': filter_source})


def articles(request, article_id):
    # Отримуємо статтю
    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        return JsonResponse({'error': 'Article not found'}, status=404)

    article_data = ArticlePreprocessor.create(article.source, article.url)

    # Перевіряємо, чи є перегляд в сесії
    viewed_articles = request.session.get('viewed_articles', [])

    if article_id not in viewed_articles:
        # Оновлюємо кількість переглядів у базі даних
        article.views += 1
        article.save(update_fields=['views'])

        # Додаємо ID статті в сесію
        viewed_articles.append(article_id)
        request.session['viewed_articles'] = viewed_articles

        # Оновлюємо кеш
        cache_key = "clusters_data"
        clusters_data = cache.get(cache_key)

        if clusters_data:
            for cluster_data in clusters_data:
                if cluster_data['cluster'].id == article.cluster_id:
                    for article_cache in cluster_data['articles']:
                        if article_cache.id == article_id:
                            article_cache.views = article.views  # Оновлюємо перегляди
                            cache.set(cache_key, clusters_data, timeout=300)  # Оновлюємо кеш
                            break

        print(article.views, 'додалося')

    return render(request, 'site_main/articles.html', {"article_content": article_data, 'views': article.views})


def map(request):
    return render(request, 'site_main/map.html')


def filter_news(request):
    if request.method == "POST" and request.is_ajax():
        sources: list = request.POST.getlist("sources[]")
        cache_key = f"clusters_data"

        res = []

        if len(sources) == 0:
            res = cache.get(cache_key)
            request.session[f'filter_source'] = 0
        else:

            for source in sources:
                res += cache.get(f"clusters_data_{source}")

            res = sorted(
                res,
                key=lambda article: article['cluster'].updated_at,  # Замінити 'date' на поле, яке містить дату статті
                reverse=True  # Від нових до старих
            )

            request.session['filter_source'] = request.POST.get("filter_source")
            request.session['filterSources'] = sources

        page_number = int(request.GET.get("page", 1))

        paginator = Paginator(res, 20)
        page_obj = paginator.get_page(page_number)

        rendered_articles = render_to_string('site_main/clusters.html', {'clusters': page_obj})
        rendered_paginator = render_to_string('site_main/paginator.html', {'clusters': page_obj})

        return JsonResponse({'articles': rendered_articles, 'paginator': rendered_paginator})

    return JsonResponse({'error': 'Invalid request'}, status=400)