import time
import uuid

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model

from clustering.models import Article, Cluster, SourceRating
from users.models import UserRecommendation
from site_main.article_preprocess import ArticlePreprocessor
from django.core.cache import cache
from clustering.utils import set_cache_cluster
from django.utils import timezone
from bson import json_util
from .utils import *
import json
from rapidfuzz import fuzz


def news(request):
    t1 = time.time()

    if request.session.get(f'filter_source') is None:
        request.session[f'filter_source'] = 0

    sources = request.session.get('filterSources')
    search_query = request.session.get("query_user")
    t3 = time.time()
    print(search_query, search_query is not '' and search_query is not None, search_query is not '', search_query is not None)
    print(sources, sources != [] and sources is not None, sources != [], sources is not None)
    if search_query is not '' and search_query is not None:
        context = get_found_news(request, search_query)
    elif sources is not []:
        print('123123123')
        context = get_filtered_news(request, sources)
    elif sources is []:
        context = get_all_news(request)

    print('user', request.user, request.user.is_authenticated, request.user.id)
    t4 = time.time()

    t2 = time.time()
    print(f'TIMEEEE - {t2 - t1}, {t4 - t3}')

    return render(request, 'site_main/index.html', context)
# def news(request):
#     t1 = time.time()
#
#     page_number = int(request.GET.get("page", 1))
#     per_page = 20
#
#     pipeline = [
#         {
#             "$facet": {
#                 "clusters": [
#                     {"$sort": {"updated_at": -1}},
#                     {"$skip": (page_number - 1) * per_page},
#                     {"$limit": per_page},
#                     {
#                         "$lookup": {
#                             "from": "clustering_article",
#                             "localField": "id",
#                             "foreignField": "cluster_id",
#                             "as": "articles"
#                         }
#                     },
#                     {
#                         "$project": {
#                             "id": 1,
#                             "updated_at": 1,
#                             "num_articles": 1,
#                             "articles.id": 1,
#                             "articles.slug": 1,
#                             "articles.title": 1,
#                             "articles.date": 1,
#                             "articles.img_url": 1,
#                             "articles.source": 1,
#                             "articles.views": 1
#                         }
#                     }
#                 ],
#                 "totalCount": [{"$count": "count"}]
#             }
#         }
#     ]
#
#     # sources
#     if request.session.get(f'filter_source') is None:
#         request.session[f'filter_source'] = 0
#
#     filter_source = request.session.get(f'filter_source')
#
#     result = list(Cluster._get_collection().aggregate(pipeline))[0]
#
#     clusters_data = result["clusters"]
#     total_count = result["totalCount"][0]["count"] if result["totalCount"] else 0
#     total_pages = (total_count + per_page - 1) // per_page
#
#     page_range = []
#     if total_pages <= 7:
#         page_range = list(range(1, total_pages + 1))
#     elif page_number <= 3:
#         page_range = list(range(1, 6)) + ["...", total_pages]
#     elif page_number >= total_pages - 2:
#         page_range = [1, "...", total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
#     else:
#         page_range = [1, "...", page_number - 2, page_number - 1, page_number, page_number + 1, page_number + 2, "...",
#                       total_pages]
#
#     MONTHS_UA = {
#         1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
#         5: "травня", 6: "червня", 7: "липня", 8: "серпня",
#         9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
#     }
#     for cluster in clusters_data:
#         for article in cluster['articles']:
#             # Перетворюємо naive datetime в aware datetime (UTC)
#             aware_date = timezone.make_aware(article['date'], timezone.get_current_timezone())
#             local_date = timezone.localtime(aware_date)
#             article['date'] = local_date.strftime(f"%H:%M, %d {MONTHS_UA[local_date.month]} %Y")
#
#     context = {
#         'clusters': clusters_data,
#         'filter': filter_source,
#         'total_count': total_count,
#         'page_number': page_number,
#         'total_pages': total_pages,
#         'page_range': page_range,
#     }
#
#     t2 = time.time()
#     print('TIMEEEE - {}'.format(t2 - t1))
#
#     return render(request, 'site_main/index.html', context)
#     # cache_key = "clusters_data"
#     # if request.session.get(f'filter_source') is None:
#     #     request.session[f'filter_source'] = 0
#     #
#     # filter_source = request.session.get(f'filter_source')
#     # sources = request.session.get('filterSources')
#     #
#     # if filter_source != 0:
#     #     clusters_data = []
#     #     for source in sources:
#     #         clusters_data += cache.get(f"clusters_data_{source}")
#     # else:
#     #     clusters_data = cache.get(cache_key)
#     #
#     # page_number = int(request.GET.get("page", 1))
#     #
#     # paginator = Paginator(clusters_data, 20, orphans=1)
#     # page_obj = paginator.get_page(page_number)
#     #
#     # return render(request, 'site_main/index.html', {'clusters': page_obj, 'filter': filter_source})


def articles(request, article_slug):
    # Отримуємо статтю
    try:
        article = Article.objects.get(slug=article_slug)

    except Article.DoesNotExist:
        return JsonResponse({'error': 'Article not found'}, status=404)

    article_data = ArticlePreprocessor.create(article.source, article.url)

    cluster = article.cluster_id
    clust = Cluster.objects.get(__raw__={'id': cluster})
    user_id = request.user.id
    if request.user.is_authenticated:
        try:
            user = UserRecommendation.objects.get(user_id=user_id)

            old_embedding = user.embedding
            new_embedding = clust.mean_embedding

            alpha = 0.4  # коефіцієнт оновлення
            user.embedding = [
                (1 - alpha) * old + alpha * new
                for old, new in zip(old_embedding, new_embedding)
            ]
            if cluster not in user.viewed_id:
                user.viewed_id.append(cluster)

            # updated_embedding = [
            #     (old_val * len(old_embedding) + new_val) / (len(old_embedding) + 1)
            #     for old_val, new_val in zip(old_embedding, clust.mean_embedding)
            # ]
            user.save()
        except Exception as ex:
            user = UserRecommendation(user_id=user_id, embedding=clust.mean_embedding, viewed_id=[cluster])
            user.save()

    # Отримуємо всі статті в цьому кластері, ordered by views for relevance
    all_articles = Article.objects(cluster_id=cluster).order_by('-date')
    articles_in_cluster = [a_articles for a_articles in all_articles if a_articles.id != article.id]

    # Перевіряємо, чи є перегляд в сесії
    viewed_articles = request.session.get('viewed_articles', [])

    if article_slug not in viewed_articles:
        # Оновлюємо кількість переглядів у базі даних
        views = article.views
        Article.objects(slug=article_slug).update_one(set__views=views+1)

        # Додаємо ID статті в сесію
        viewed_articles.append(article_slug)
        request.session['viewed_articles'] = viewed_articles

        # Оновлюємо кеш
        # cache_key = "clusters_data"
        # clusters_data = cache.get(cache_key)
        #
        # if clusters_data:
        #     for cluster_data in clusters_data:
        #         if cluster_data['cluster']['id'] == article.cluster_id:
        #             for article_cache in cluster_data['articles']:
        #                 if article_cache['slug'] == article_slug:
        #                     article_cache['views'] = article.views  # Оновлюємо перегляди
        #                     cache.set(cache_key, clusters_data, timeout=300)  # Оновлюємо кеш
        #                     break
        #
        # print(article.views, 'додалося')
    try:
        source_rat = SourceRating.objects.get(__raw__={'source': article_data['source_title']})
        source_rating = source_rat.rating / source_rat.num_rating
    except:
        source = SourceRating(source=article_data['source_title'], rating=0, num_rating=0)
        source_rating = 0
        source.save()

    return render(request, 'site_main/articles.html',
                  {"article_content": article_data,
                   'views': article.views,
                   'articles_in_cluster': articles_in_cluster,
                   'source_rat': source_rating})


def map(request):
    return render(request, 'site_main/map.html')


def filter_news(request):
    if request.method == "POST":
        sources = request.POST.getlist("sources[]")

        context = get_filtered_news(request, sources)

        request.session['filter_source'] = request.POST.get("filter_source")
        request.session['filterSources'] = sources

        rendered_articles = render_to_string('site_main/clusters.html', context)
        rendered_paginator = render_to_string('site_main/paginator.html', context)

        return JsonResponse({'articles': rendered_articles, 'paginator': rendered_paginator})

    return JsonResponse({'error': 'Invalid request'}, status=400)


def rating(request):
    if request.method == "POST":
        source_get = request.POST.get('source')
        rating_get = request.POST.get('rating_post')

        try:
            source = SourceRating.objects.get(__raw__={'source': source_get})
            source.rating = (source.rating + float(rating_get))
            source.num_rating = source.num_rating + 1
            result = source.rating / source.num_rating
            source.save()
        except Exception as ex:
            print(ex)
            source = SourceRating(source=source_get, rating=rating_get, num_rating=1)
            result = source.rating / source.num_rating
            source.save()

        res = f'<div class="Stars" style="--rating: {result};"></div>'

        return JsonResponse({'rating_n': res})


def search_news(request):
    if request.method == "POST":
        search_query = request.GET.get("query", request.POST.get("query", "")).strip()
        cq = request.POST.get('clear_query')

        # If query is empty, return all news
        if not search_query:
            return JsonResponse({'articles': '<h1 class="no-one-finned">Нічого не знайдено</h1>', 'paginator': ''})

        if cq == '1':
            request.session['query_user'] = ''
            context = get_all_news(request)
        elif cq == '0':
            context = get_found_news(request, search_query)
            request.session['query_user'] = search_query

        if context['total_count'] == 0:
            return JsonResponse({'articles': '<h1 class="no-one-finned">Нічого не знайдено</h1>', 'paginator': ''})

        rendered_articles = render_to_string('site_main/clusters.html', context)
        rendered_paginator = render_to_string('site_main/paginator.html', context)

        return JsonResponse({'articles': rendered_articles, 'paginator': rendered_paginator})


def main(request):
    t1 = time.time()

    page_number = int(request.GET.get("page", 1))
    per_page = 20

    if request.user.is_authenticated:
        clusters_for_user = get_recommendation_clusters(request.user.id)
    else:
        clusters_for_user = get_all_news(request)['clusters']

    clusters_best_today = get_trending_clusters()
    clusters_data = get_all_news(request)['clusters']

    t2 = time.time()
    print(f'TIMEEEE MAIN PAGEEEEE - {t2 - t1} seconds')

    # clusters_for_user
    # clusters_best_today
    return render(request, 'site_main/main.html', {'clusters_for_user': clusters_for_user,
                                                   'clusters_best_today': clusters_best_today,
                                                   'clusters_new': clusters_data}
                  )
