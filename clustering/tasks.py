# clustering/tasks.py
from celery import shared_task
from django.core.cache import cache

from .clustering_ai import parse_and_update_clusters
from .utils import set_cache_cluster, set_cache_filtered_source


@shared_task
def parse_and_update_clusters_task(similarity_threshold=0.7):
    parse_and_update_clusters(similarity_threshold)
    print('Finished parse_and_update_clusters_task')

    set_cache_cluster()
    sources = ['tsn', 'unian', 'radio_svoboda']
    for source in sources:
        set_cache_filtered_source(source)
        print('finished set_cache_filtered_source {}'.format(source))

    print('Finished cache set')

