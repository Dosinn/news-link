#!/usr/bin/env python3
# parse_and_cluster.py

import re
import time
from typing import Any, Awaitable

import pytz
import torch
import redis
import logging
from datetime import datetime, UTC
from pymongo import MongoClient, DESCENDING, ASCENDING, UpdateOne, InsertOne
from sentence_transformers import SentenceTransformer
from bson.objectid import ObjectId
from parser import Parsing  # Ensure this is the correct path to your Parsing class
from tqdm import tqdm
from slugify import slugify
from bson import json_util
import json
import pickle
from datetime import timedelta
import numpy as np

# ----------------------------- Configuration -----------------------------

# MongoDB Configuration
MONGO_URI = 'mongodb+srv://dosi:hGUu7HixfbVFYdEU@cluster0.kyhro.mongodb.net/NewsLink?retryWrites=true&w=majority'
MONGO_DB_NAME = 'NewsLink'

# Redis Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 1

# Clustering Configuration
SIMILARITY_THRESHOLD = 0.7

# Model Configuration
MODEL_PATH = '/home/ubuntu/news-link/clustering/static/best_model'  # Adjust the path if necessary

# Timezone Configuration
TIMEZONE = 'Europe/Kiev'

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("parse_and_cluster.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ----------------------------- Initialization -----------------------------

# Initialize MongoDB Client
mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=50000)
db = mongo_client[MONGO_DB_NAME]
articles_collection = db['clustering_article']
clusters_collection = db['clustering_cluster']

# Initialize Redis Client
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

# Initialize Sentence Transformer Model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
logger.info(f'Using device: {device}')
model = SentenceTransformer(MODEL_PATH, device=device)

# Month Mapping
MONTHS_UA = {
    "січня": "01", "лютого": "02", "березня": "03", "квітня": "04",
    "травня": "05", "червня": "06", "липня": "07", "серпня": "08",
    "вересня": "09", "жовтня": "10", "листопада": "11", "грудня": "12"
}

MONTHS_UA_A = {
    1: "січня",
    2: "лютого",
    3: "березня",
    4: "квітня",
    5: "травня",
    6: "червня",
    7: "липня",
    8: "серпня",
    9: "вересня",
    10: "жовтня",
    11: "листопада",
    12: "грудня",
}


# ----------------------------- Helper Functions -----------------------------
def parse_date(date_str):
    """
    Converts date strings with Ukrainian month names into timezone-aware datetime objects.
    """
    # Replace Ukrainian month names with numbers
    for ua_month, num_month in MONTHS_UA.items():
        if ua_month in date_str:
            date_str = date_str.replace(ua_month, num_month)
            break  # Assume only one month name per date string

    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        pass  # If it's not ISO 8601, continue with other formats

    # Supported date formats
    supported_formats = [
        "%H:%M, %d %m %Y",
        "%H:%M, %d.%m.%Y",
        "%H:%M, %d.%m.%y",
    ]

    for fmt in supported_formats:
        try:
            # # Parse as naive time
            # naive_date = datetime.strptime(date_str, fmt)
            #
            # # --- FIX START ---
            # # Assuming naive time from these formats is actually UTC
            # utc_aware_date = pytz.utc.localize(naive_date)
            #
            # # Convert from UTC to the target timezone (Europe/Kiev)
            # timezone = pytz.timezone(TIMEZONE)
            # aware_date = utc_aware_date.astimezone(timezone)

            naive_date = datetime.strptime(date_str, fmt)
            timezone = pytz.timezone(TIMEZONE)
            aware_date = timezone.localize(naive_date)
            return aware_date
        except ValueError:
            continue

    logger.error(f"Unsupported date format: {date_str}")
    raise ValueError(f"Unsupported date format: {date_str}")


def preprocess_text(text):
    """
    Preprocesses text by lowercasing and removing unwanted characters.
    """
    text = text.lower()
    text = re.sub(r'[^а-яіїa-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_embedding(text):
    """
    Generates embedding for the given text using the SentenceTransformer model.
    """
    text = preprocess_text(text)
    if not text:
        return None
    embedding = model.encode(text, convert_to_tensor=True, show_progress_bar=False)
    return embedding.cpu().tolist()


def cosine_similarity(vec1, vec2):
    """
    Calculates cosine similarity between two vectors.
    """
    v1 = torch.tensor(vec1)
    v2 = torch.tensor(vec2)
    return torch.cosine_similarity(v1, v2, dim=0).item()


def get_formatted_date(date_str):
    """
    Форматує дату у вигляді: 15:18, 02 січня 2025 (локальний час)
    """
    # Вказати часовий пояс
    local_tz = pytz.timezone("Europe/Kyiv")

    # Перетворення часу в локальний часовий пояс
    local_date = date_str.astimezone(local_tz)

    # Форматування дати
    return local_date.strftime(f"%H:%M, %d {MONTHS_UA_A[local_date.month]} %Y")


def get_next_id_article():
    # Отримуємо найбільший поточний _id з колекції
    max_id_doc = articles_collection.find_one(sort=[("id", -1)])  # Сортуємо у зворотному порядку
    if max_id_doc is None:
        return 1  # Якщо колекція порожня, починаємо з 1
    return max_id_doc["id"] + 1  # Повертаємо найбільший _id + 1


def get_next_id_cluster():
    # Отримуємо найбільший поточний _id з колекції
    max_id_doc = clusters_collection.find_one(sort=[("id", -1)])  # Сортуємо у зворотному порядку
    if max_id_doc is None:
        return 1  # Якщо колекція порожня, починаємо з 1
    return max_id_doc["id"] + 1  # Повертаємо найбільший _id + 1


# ----------------------------- Cache Functions -----------------------------


def set_cache_cluster(sources: list, ids_all: list = [], ids_updated: list = []):
    logger.info('skip cashing')
    # t5 = time.time()
    # if not ids_all:
    #     logger.info("No clusters to update, skipping cache update.")
    #     return
    #
    # """
    # Fetches all clusters and their associated articles, formats the dates,
    # and caches the data in Redis.
    # """
    #
    # clusters_data = {
    #     ":1:clusters_data": pickle.loads(redis_client.get(":1:clusters_data")) if redis_client.get(":1:clusters_data") else [],
    # }
    # for source in sources:
    #     clusters_data.setdefault(f':1:clusters_data_{source}', pickle.loads(redis_client.get(f':1:clusters_data_{source}')) if redis_client.get(f":1:clusters_data_{source}") else [])
    #     clusters_data.setdefault(f'source_ids_{source}', set())
    #
    # if not clusters_data[':1:clusters_data']:
    #     # clusters = list(clusters_collection.find().sort('updated_at', DESCENDING))
    #     clusters = list(clusters_collection.find().sort('updated_at', DESCENDING))
    # else:
    #     clusters = list(clusters_collection.find({'id': {'$in': ids_all}}).sort('updated_at', DESCENDING))
    #
    # for cluster in clusters:
    #     articles = list(articles_collection.find({'cluster_id': cluster['id']}))
    #     articles.sort(key=lambda x: x['date'], reverse=True)
    #     # Format dates
    #     for article in articles:
    #
    #         if isinstance(article.get('date'), datetime):
    #             article['date'] = get_formatted_date(article['date'])
    #         else:
    #             article['date'] = str(article.get('date'))
    #
    #     cluster_object = {
    #         'cluster': {
    #             'id': cluster['id'],
    #             'created_at': cluster['created_at'],
    #             'updated_at': cluster['updated_at'],
    #         },
    #         'articles': articles,
    #         'articles_count': len(articles),
    #         'first_article': articles[0] if articles else None
    #     }
    #
    #     if cluster['id'] in ids_updated:
    #         for i, existing_cluster in enumerate(clusters_data[":1:clusters_data"]):
    #             if existing_cluster['cluster']['id'] == cluster['id']:
    #                 clusters_data[":1:clusters_data"][i] = cluster_object
    #                 logger.info('updated cluster {}'.format(cluster['id']))
    #                 break
    #
    #         sources_processed = []
    #
    #         for article in articles:
    #             logger.info(f'{article['source']} {cluster['id']}')
    #             if article['source'] not in sources_processed:
    #                 for i, existing_cluster in enumerate(clusters_data[f":1:clusters_data_{article['source']}"]):
    #                     if existing_cluster['cluster']['id'] == article['cluster_id']:
    #                         clusters_data[f":1:clusters_data_{article['source']}"][i] = cluster_object
    #                         logger.info(f'updated cluster source - {article['source']} {cluster['id']}')
    #                         sources_processed.append(article['source'])
    #                         break
    #     else:
    #         clusters_data[":1:clusters_data"].append(cluster_object)
    #
    #         for article in articles:
    #             if article['cluster_id'] not in clusters_data[f'source_ids_{article["source"]}']:
    #
    #                 filtered_articles = [article for article in articles if article['source'] in sources]
    #                 other_articles = [article for article in articles if article['source'] not in sources]
    #
    #                 if filtered_articles:
    #                     cluster_object['first_article'] = filtered_articles[0]
    #
    #                     if cluster_object['articles_count'] > 1:
    #                         cluster_object['articles'] = filtered_articles + other_articles
    #
    #                 clusters_data[f":1:clusters_data_{article["source"]}"].append(cluster_object)
    #                 clusters_data[f'source_ids_{article["source"]}'].add(article['cluster_id'])
    #
    # # sorting
    # clusters_data[":1:clusters_data"].sort(key=lambda x: x['cluster']['updated_at'], reverse=True)
    #
    # for source in sources:
    #     clusters_data[f":1:clusters_data_{source}"].sort(key=lambda x: x['cluster']['updated_at'], reverse=True)
    #
    # redis_client.set(":1:clusters_data", pickle.dumps(clusters_data[":1:clusters_data"]))
    # logger.info('Finished setting cache for clusters')
    #
    # for source in sources:
    #     redis_client.set(f':1:clusters_data_{source}', pickle.dumps(clusters_data[f':1:clusters_data_{source}']))
    #     logger.info('Finished setting cache for clusters source: {}'.format(source))
    #
    # logger.info(f'finished setting cache for clusters. TIME - {time.time() - t5}')


# def set_cache_filtered_source(source):
#     """
#     Filters clusters based on the specified source and caches the filtered data.
#     """
#     cache_key_source = f":1:clusters_data_{source}"
#     logger.info(f"Setting cache for source: {source}")
#     cache_key = ":1:clusters_data"
#
#     try:
#         clusters_data_json = redis_client.get(cache_key)
#         if not clusters_data_json:
#             logger.warning("No clusters data found in cache.")
#             return
#
#         clusters_data = pickle.loads(clusters_data_json)
#         res = []
#         res2 = []
#
#         # Only clusters with more than one article
#         clusters = list(clusters_collection.find({'num_articles': {'$gt': 1}}))
#         for cluster in clusters:
#             articles = list(articles_collection.find({'cluster_id': cluster['id']}))
#             formatted_articles = []
#             for article in articles:
#                 if isinstance(article.get('date'), datetime):
#                     article['date'] = get_formatted_date(article['date'])
#                 else:
#                     article['date'] = str(article.get('date'))
#                 formatted_articles.append(article)
#             res2.append({
#             	'cluster': {
#                     'id': cluster['id'],
#                     'created_at': cluster['created_at'],
#                     'updated_at': cluster['updated_at'],
#                 },
#                 'articles': formatted_articles,
#                 'articles_count': len(formatted_articles),
#                 'first_article': formatted_articles[0] if formatted_articles else None
#             })
#
#         redis_client.set(':1:only_cluster', pickle.dumps(res2), ex=400)
#
#         for cluster_data in clusters_data:
#             filtered_articles = [article for article in cluster_data['articles'] if article['source'] in source]
#             other_articles = [article for article in cluster_data['articles'] if article['source'] not in source]
#
#             if filtered_articles:
#                 cluster_data['first_article'] = filtered_articles[0]
#
#                 if len(cluster_data['articles']) > 1:
#                     cluster_data['articles'] = filtered_articles + other_articles
#
#                 res.append(cluster_data)
#
#         redis_client.set(cache_key_source, pickle.dumps(res), ex=400)
#         logger.info(f"Finished setting cache for filtered source: {source}, {cache_key_source}")
#     except Exception as e:
#         logger.error(f"Error setting cache for filtered source {source}: {e}")


# ----------------------------- Main Function -----------------------------

def parse_and_update_clusters(similarity_threshold=SIMILARITY_THRESHOLD):
    """
    Orchestrates the parsing, inserting articles, updating clusters,
    and refreshing the cache.
    """
    # 1. Parsing News

    updated_cluster_ids = []
    all_cluster_ids = []

    logger.info("...Starting parsing...")
    parser = Parsing()
    parser.tsn(1)
    parser.unian()
    parser.radio_svoboda()
    parser.ukrinform()
    parser.interfax()
    news_items = parser.news  # Assuming this returns a list of ArticleParser instances
    logger.info(f"Parsed {len(news_items)} news items.")

    # 2. Inserting New Articles
    new_articles_count = 0
    new_articles = []

    for news_item in tqdm(news_items, desc='Inserting new articles'):
        try:
            if articles_collection.find_one({'url': news_item.url}):
                continue
            try:
                parsed_date = parse_date(news_item.date)
            except ValueError as e:
                logger.error(f"Date parsing error '{news_item.date}' for article '{news_item.title}': {e}")
                continue

            article = {
                'id': get_next_id_article(),
                'slug': slugify(news_item.title),
                'title': news_item.title,
                'url': news_item.url,
                'date': parsed_date,
                'img_url': news_item.img_url,
                'source': news_item.source,
                'views': 0,
                'cluster_id': None
            }
            result = articles_collection.insert_one(article)
            article['_id'] = result.inserted_id
            new_articles.append(article)
            new_articles_count += 1
        except Exception as e:
            logger.error(f"Failed to add article '{news_item.title}' due to error: {e}")

    logger.info(f"Added {new_articles_count} new articles.")

    if new_articles_count == 0:
        logger.info("No new articles to cluster.")
        logger.info("Updating cache...")
        sources = ['tsn', 'unian', 'radio_svoboda', 'ukrinform', 'interfax']
        logger.info(f'POST UPDATED IDS - {updated_cluster_ids}')
        logger.info(f'POST ALL IDS - {all_cluster_ids}')
        set_cache_cluster(sources=sources, ids_updated=updated_cluster_ids, ids_all=all_cluster_ids)
        logger.info("Cache update completed.")
        return

    # 3. Updating Clusters
    logger.info("Updating clusters...")
    try:
        # Поточний час
        now = datetime.now(UTC)

        # Часова межа (останні 2 дні)
        time_threshold = now - timedelta(days=2)

        # Отримання статей без кластерів
        unclustered_articles = list(
            articles_collection.find({'cluster_id': None}).sort('date', ASCENDING)
        )

        # Отримання кластерів за останні 2 дні
        clusters = list(
            clusters_collection.find({'created_at': {'$gte': time_threshold}})
        )

        for article in tqdm(unclustered_articles, desc='Clustering articles'):
            article_embedding = get_embedding(article['title'])
            if not article_embedding:
                logger.warning(f"Skipped article without text: {article['title']}")
                continue

            best_cluster = None
            best_similarity = -1

            for cluster in clusters:
                sim = cosine_similarity(article_embedding, cluster['mean_embedding'])
                if sim >= similarity_threshold and sim > best_similarity:
                    best_similarity = sim
                    best_cluster = cluster

            if best_cluster:
                # Update mean_embedding incrementally
                current_mean = torch.tensor(best_cluster['mean_embedding'])
                new_embedding = torch.tensor(article_embedding)
                updated_mean = (current_mean * best_cluster['num_articles'] + new_embedding) / (
                        best_cluster['num_articles'] + 1)
                updated_mean = updated_mean.tolist()

                # cluster_bulk_writes.append(
                #     UpdateOne(
                #         {'_id': best_cluster['_id']},  # Фільтр: шукаємо кластер за його _id
                #         {'$set': {'mean_embedding': updated_mean, 'updated_at': datetime.now(UTC)},
                #          '$inc': {'num_articles': 1}}  # Оновлюємо mean_embedding, updated_at та збільшуємо лічильник
                #     )
                # )

                # Update cluster in MongoDB
                clusters_collection.update_one(
                    {'_id': best_cluster['_id']},
                    {'$set': {'mean_embedding': updated_mean, 'updated_at': datetime.now(UTC)},
                     '$inc': {'num_articles': 1}}
                )

                updated_cluster_ids.append(best_cluster['id'])
                all_cluster_ids.append(best_cluster['id'])

                # article_bulk_writes.append(
                #     UpdateOne(
                #         {'_id': article['_id']},  # Фільтр: шукаємо статтю за її _id
                #         {'$set': {'cluster_id': best_cluster['id']}}  # Встановлюємо cluster_id
                #     )
                # )

                # # Update article with cluster_id
                articles_collection.update_one(
                    {'_id': article['_id']},
                    {'$set': {'cluster_id': best_cluster['id']}}
                )

                logger.info(
                    f"Added article '{article['title']}' to cluster {best_cluster['id']} with similarity {best_similarity:.2f}")
            else:
                new_cluster_id = get_next_id_cluster()
                # Create a new cluster
                new_cluster = {
                    'id': new_cluster_id,
                    'mean_embedding': article_embedding,
                    'created_at': datetime.now(UTC),
                    'updated_at': datetime.now(UTC),
                    'num_articles': 1
                }
                # cluster_bulk_writes.append(InsertOne(new_cluster))
                clusters_collection.insert_one(new_cluster)
                clusters.append(clusters_collection.find_one({'id': new_cluster_id}))
                # article_bulk_writes.append(
                #     UpdateOne(
                #         {'_id': article['_id']},
                #         {'$set': {'cluster_id': new_cluster_id}}
                #     )
                # )

                all_cluster_ids.append(new_cluster_id)

                # Update article with new cluster_id
                articles_collection.update_one(
                    {'_id': article['_id']},
                    {'$set': {'cluster_id': new_cluster_id}}
                )

                logger.info(f"Created new cluster {new_cluster_id} for article '{article['title']}'")

        logger.info("Cluster update process completed.")
    except Exception as e:
        logger.error(f"Error during clustering: {e}")
        return

    # 4. Updating Cache
    logger.info("Updating cache...")
    logger.info(f'POST UPDATED IDS - {updated_cluster_ids}')
    logger.info(f'POST ALL IDS - {all_cluster_ids}')
    sources = ['tsn', 'unian', 'radio_svoboda', 'ukrinform', 'interfax']
    set_cache_cluster(sources=sources, ids_updated=updated_cluster_ids, ids_all=all_cluster_ids)
    logger.info("Cache update completed.")




# ----------------------------- Entry Point -----------------------------

if __name__ == "__main__":
    try:
        t1 = time.time()
        parse_and_update_clusters()
        t2 = time.time()
        logger.info(f"TIME - {t2 - t1}")
    except Exception as e:
        logger.critical(f"Critical error in parse_and_update_clusters: {e}", exc_info=True)
