
from django.core.cache import cache
from .models import Cluster


def set_cache_cluster():
    cache_key = f"clusters_data"
    clusters_data = []

    contact_list = Cluster.objects.prefetch_related('articles').all().order_by('-updated_at')

    for cluster in contact_list:
        articles_clus = list(cluster.articles.all())

        # Заміна дати на форматований текстовий вигляд
        for article in articles_clus:
            article.date = article.get_formatted_date()  # Заміна дати у полі `date`

        clusters_data.append({
            'cluster': cluster,
            'articles': articles_clus,
            'articles_count': len(articles_clus),
            'first_article': articles_clus[0] if articles_clus else None
        })
    cache.set(cache_key, clusters_data, timeout=300)  # todo поміняти і синхронізувати час із Celery


def set_cache_filtered_source(source):
    cache_key_source = f"clusters_data_{source}"
    print(cache_key_source)
    cache_key = f"clusters_data"
    clusters_data = cache.get(cache_key)
    res = []
    res2 = []
    contact = Cluster.objects.prefetch_related('articles').filter(num_articles__gt=1)
    for cluster_real in contact:
        articles_clus = list(cluster_real.articles.all())
        res2.append({
            'cluster': cluster_real,
            'articles': articles_clus,
            'articles_count': len(articles_clus),
            'first_article': articles_clus[0] if articles_clus else None
        })

    cache.set('only_cluster', res2, timeout=300)

    for cluster in clusters_data:
        filtered_articles = [article for article in cluster['articles'] if article.source in source]
        other_articles = [article for article in cluster['articles'] if article.source not in source]

        if filtered_articles:
            cluster['first_article'] = filtered_articles[0]

            if len(cluster['articles']) > 1:
                cluster['articles'] = filtered_articles + other_articles

            if cluster not in res:
                res.append(cluster)

    cache.set(cache_key_source, res, timeout=300)
