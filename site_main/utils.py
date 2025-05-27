from clustering.models import Article, Cluster
import time
import re
from datetime import timedelta
from django.utils.timezone import now
import numpy as np
from users.models import UserRecommendation

PER_PAGE = 20


def get_filtered_news(request, sources):
    page_number = int(request.GET.get("page", 1))

    selected_sources = sources if sources else []

    pipeline = [
        # 1. Отримати всі статті для кожного кластера
        {
            "$lookup": {
                "from": "clustering_article",
                "localField": "id",  # Поле ID у колекції кластерів
                "foreignField": "cluster_id",  # Поле ID кластера у колекції статей
                "as": "articles"  # Назва нового масиву зі статтями
            }
        }
    ]

    if selected_sources:
        pipeline.append(
            {
                "$match": {
                    # Фільтруємо кластери: залишаємо ті, де хоча б одна стаття
                    # в масиві 'articles' має 'source' зі списку selected_sources
                    "articles.source": {"$in": selected_sources}
                }
            }
        )

    # 3. Додати решту етапів (пагінація, форматування, підрахунок)
    pipeline.extend([
        {
            # Використовуємо $facet для одночасного отримання даних з пагінацією
            # та загальної кількості відфільтрованих документів
            "$facet": {
                "data": [  # Гілка для отримання даних поточної сторінки
                    # 3a. Сортування відфільтрованих кластерів
                    {
                        "$sort": {"updated_at": -1}
                    },
                    # 3b. Пропуск документів для пагінації
                    {
                        "$skip": (page_number - 1) * PER_PAGE
                    },
                    # 3c. Обмеження кількості документів на сторінці
                    {
                        "$limit": PER_PAGE
                    },
                    # 3d. Додавання/оновлення полів для фінального вигляду
                    {
                        "$addFields": {
                            # Рахуємо кількість статей у КОЖНОМУ кластері, що залишився
                            "articles_count": {"$size": "$articles"},
                            # Форматуємо дати у всіх статтях кластера
                            "articles": {
                                "$map": {
                                    "input": "$articles",
                                    "as": "article",
                                    "in": {
                                        "$mergeObjects": [
                                            "$$article",
                                            {
                                                "date": {
                                                    "$dateToString": {
                                                        "date": "$$article.date",
                                                        "format": "%H:%M, %d.%m.%Y",
                                                        "timezone": "Europe/Kiev"
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    },
                    # 3e. Проекція потрібних полів (опціонально, для чистоти)
                    # Перейменовуємо _id на id і прибираємо _id за замовчуванням
                    {
                        "$project": {
                            "_id": 0,  # Прибрати стандартне поле _id
                            "id": "$_id",  # Створити поле 'id' зі значенням '_id'
                            "updated_at": 1,
                            "num_articles": 1,  # Оригінальне поле кількості статей (якщо воно є в кластері)
                            "articles": 1,  # Повний масив статей для цього кластера
                            "articles_count": 1  # Поле з кількістю статей, розраховане вище
                        }
                    }
                ],
                "totalCount": [  # Гілка для підрахунку загальної кількості
                    # Рахуємо кількість документів, що пройшли $match (фільтрацію)
                    {
                        "$count": "count"
                    }
                ]
            }
        },
        # 4. Фінальна проекція для зручного формату виводу
        {
            "$project": {
                "clusters": "$data",  # Масив кластерів поточної сторінки
                # Безпечне отримання загальної кількості (поверне 0, якщо немає результатів)
                "totalCount": {"$ifNull": [{"$arrayElemAt": ["$totalCount.count", 0]}, 0]}
            }
        }
    ])

    return pagination(request, pipeline, '')


def get_all_news(request):
    t1 = time.time()
    page_number = int(request.GET.get("page", 1))

    pipeline = [
        {
            "$facet": {
                "clusters": [
                    {
                        "$sort": {"updated_at": -1}
                    },
                    {
                        "$skip": (page_number - 1) * PER_PAGE
                    },
                    {
                        "$limit": PER_PAGE
                    },
                    {
                        "$lookup": {
                            "from": "clustering_article",
                            "localField": "id",
                            "foreignField": "cluster_id",
                            "as": "articles"
                        }
                    },
                    {
                        "$project": {
                            "id": 1,
                            "updated_at": 1,
                            "num_articles": 1,
                            "articles": 1  # Залишаємо articles, але видаляємо непотрібні підполя
                        }
                    },
                    {
                        "$addFields": {
                            "articles": {
                                "$map": {
                                    "input": "$articles",
                                    "as": "article",
                                    "in": {
                                        "$mergeObjects": [
                                            "$$article",
                                            {
                                                "date": {
                                                    "$dateToString": {
                                                        "date": "$$article.date",
                                                        "format": "%H:%M, %d.%m.%Y",
                                                        "timezone": "Europe/Kiev"
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            },
                            "articles_count": {"$size": "$articles"}
                        }
                    }
                ],
                "totalCount": [
                    {
                        "$count": "count"
                    }
                ]
            }
        }
    ]
    t2 = time.time()

    print('ttttttttttttttttttttt', t2-t1)
    return pagination(request, pipeline, '')


def get_found_news(request, search_query):
    """
    Searches for news clusters containing articles matching a query in their title
    using MongoDB aggregation and handles pagination.
    """
    page_number = int(request.GET.get("page", 1))

    print(f"Searching for query: '{search_query}' on page {page_number}")

    # If query is empty, return all news

    # Escape special regex characters in the search query
    # This prevents issues if the user searches for things like '.', '*', '+', etc.
    escaped_query = re.escape(search_query)

    pipeline = [
        # 1. Get all articles for each cluster
        {
            "$lookup": {
                "from": "clustering_article", # Ensure this is the correct collection name for articles
                "localField": "id",
                "foreignField": "cluster_id",
                "as": "articles"
            }
        },
        # 2. Filter clusters: keep only those where at least one article title
        #    matches the search query (case-insensitive partial match)
        {
            "$match": {
                "articles.title": { "$regex": escaped_query, "$options": "i" }
            }
        },
        # 3. Use $facet for simultaneous pagination and counting
        {
            "$facet": {
                "data": [  # Branch for paginated data
                    # 3a. Sort filtered clusters by update time
                    {
                        "$sort": {"updated_at": -1}
                    },
                    # 3b. Skip documents for pagination
                    {
                        "$skip": (page_number - 1) * PER_PAGE
                    },
                    # 3c. Limit documents on the page
                    {
                        "$limit": PER_PAGE
                    },
                     # 3d. Add/update fields for the final output
                    {
                        "$addFields": {
                            # Calculate the count of articles in the cluster (after initial lookup)
                            "articles_count": {"$size": "$articles"},
                             # Format dates within the articles array
                            "articles": {
                                "$map": {
                                    "input": "$articles",
                                    "as": "article",
                                    "in": {
                                        "$mergeObjects": [
                                            "$$article",
                                            {
                                                "date": {
                                                    "$dateToString": {
                                                        "date": "$$article.date",
                                                        "format": "%H:%M, %d.%m.%Y",
                                                        "timezone": "Europe/Kiev"
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    },
                     # 3e. Project the required fields and rename _id to id
                    {
                        "$project": {
                            "_id": 0, # Exclude the default _id field
                            "id": "$_id", # Create 'id' field from _id
                            "updated_at": 1,
                            "num_articles": 1, # Include original num_articles if needed
                            "articles": 1, # Keep the articles array
                            "articles_count": 1 # Keep the calculated count
                        }
                    }
                ],
                "totalCount": [  # Branch for total count
                    # Count the number of documents that passed the $match stage
                    {
                        "$count": "count"
                    }
                ]
            }
        },
        # 4. Final projection to format the output structure
        {
            "$project": {
                "clusters": "$data", # The paginated clusters
                # Get the total count safely, defaulting to 0
                "totalCount": {"$ifNull": [{"$arrayElemAt": ["$totalCount.count", 0]}, 0]}
            }
        }
    ]

    # The pagination helper function executes the pipeline and formats the context
    return pagination(request, pipeline, search_query)


def pagination(request, pipeline, search):
    t3 = time.time()
    page_number = int(request.GET.get("page", 1))
    result = list(Cluster._get_collection().aggregate(pipeline))[0]

    clusters_data = result["clusters"]
    try:
        total_count = result["totalCount"][0]["count"] if result["totalCount"] else 0
    except TypeError:
        total_count = result["totalCount"] if result["totalCount"] else 0
    total_pages = (total_count + PER_PAGE - 1) // PER_PAGE

    page_range = []
    if total_pages <= 7:
        page_range = list(range(1, total_pages + 1))
    elif page_number <= 3:
        page_range = list(range(1, 6)) + ["...", total_pages]
    elif page_number >= total_pages - 2:
        page_range = [1, "...", total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
    else:
        page_range = [1, "...", page_number - 2, page_number - 1, page_number, page_number + 1, page_number + 2,
                      "...",
                      total_pages]
    t4 = time.time()
    context = {
        'clusters': clusters_data,
        'filter': request.session.get('filter_source'),
        'query_user': f'{search}',
        'total_count': total_count,
        'page_number': page_number,
        'total_pages': total_pages,
        'page_range': page_range,
    }
    t5 = time.time()
    print('pppppppppppp', t4-t3, t5-t3)

    return context


def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))


def get_recommendation_clusters(user_id, limit=10):
    user = UserRecommendation.objects(user_id=user_id).first()
    if not user or not user.embedding:
        return []

    user_vec = np.array(user.embedding)
    yesterday = now() - timedelta(days=1)

    # Кластери, оновлені за останній день
    clusters = Cluster.objects(updated_at__gte=yesterday)

    # Фільтруємо в Python — тільки ті, що не в user.viewed_id
    filtered_clusters = [cl for cl in clusters if cl.id not in user.viewed_id]

    scored_clusters = []
    for cluster in filtered_clusters:
        sim = cosine_similarity(user_vec, cluster.mean_embedding)
        scored_clusters.append((sim, cluster))

    scored_clusters.sort(reverse=True, key=lambda x: x[0])
    top_clusters = [cl for _, cl in scored_clusters[:limit]]
    return top_clusters


def get_trending_clusters(limit=10):
    yesterday = now() - timedelta(days=1)

    # Отримуємо кластери, оновлені за останній день
    clusters = Article.objects(date__gte=yesterday)

    # Сортуємо за кількістю переглядів (наприклад, поле `views`)
    sorted_clusters = sorted(clusters, key=lambda cl: cl.views, reverse=True)

    res = []

    for i in sorted_clusters[:limit]:
        res.append(Cluster.objects.get(__raw__={'id': i.cluster_id}))

    # Повертаємо топ N
    return res