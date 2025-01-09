# clustering/clustering_ai.py
import os
import torch
from sentence_transformers import SentenceTransformer
from django.utils import timezone
from .models import Article, Cluster
from clustering.parser import Parsing  # Ваш парсер
import re
from datetime import datetime
from django.utils.timezone import make_aware
import pytz


def parse_date(date_str):
    # Ваш словник місяців
    MONTHS_UA = {
        "січня": "01", "лютого": "02", "березня": "03", "квітня": "04",
        "травня": "05", "червня": "06", "липня": "07", "серпня": "08",
        "вересня": "09", "жовтня": "10", "листопада": "11", "грудня": "12"
    }

    # Заміна текстових місяців
    for ua_month, num_month in MONTHS_UA.items():
        if ua_month in date_str:
            date_str = date_str.replace(ua_month, num_month)

    # Список підтримуваних форматів
    supported_formats = [
        "%H:%M, %d %m %Y",  # Формат з пробілами (повний рік)
        "%H:%M, %d.%m.%Y",  # Формат з крапками (повний рік)
        "%H:%M, %d.%m.%y",  # Формат з крапками (короткий рік)
    ]

    for fmt in supported_formats:
        try:
            naive_date = datetime.strptime(date_str, fmt)
            timezone = pytz.timezone('Europe/Kiev')  # Установлення часового поясу
            return make_aware(naive_date, timezone)
        except ValueError:
            continue

    raise ValueError(f"Непідтримуваний формат дати: {date_str}")


# Налаштування пристрою та моделі
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, 'static', 'best_model')

# Завантаження моделі
model = SentenceTransformer(model_path, device=device)


# Препроцесинг тексту
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^а-яіїa-z0-9\s]', '', text)  # Дозволені символи
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_embedding(text):
    text = preprocess_text(text)
    if not text:  # Якщо текст порожній
        return None
    embedding = model.encode(text, convert_to_tensor=True, show_progress_bar=False)
    return embedding.cpu().tolist()


# Косинусна схожість
def cosine_similarity(vec1, vec2):
    v1 = torch.tensor(vec1)
    v2 = torch.tensor(vec2)
    return torch.cosine_similarity(v1, v2, dim=0).item()


def parse_and_update_clusters(similarity_threshold=0.7):
    # 1. Парсинг новин
    print("...Запуск парсингу...")
    tt = Parsing()
    tt.tsn(1)
    tt.unian()
    tt.radio_svoboda()

    # 2. Додавання нових статей у базу даних (без ембеддінгів)
    new_articles_count = 0
    new_articles = []
    for news_item in tt.news:
        try:
            if Article.objects.filter(url=news_item.url).exists():
                continue
            try:
                parsed_date = parse_date(news_item.date)
            except ValueError as e:
                print(f"Помилка обробки дати '{news_item.date}' для статті '{news_item.title}': {e}")
                continue

            article = Article.objects.create(
                title=news_item.title,
                url=news_item.url,
                date=parsed_date,
                img_url=news_item.img_url,
                source=news_item.source
            )

            new_articles.append(article)
            new_articles_count += 1

        except Exception as e:
            print(f"Не вдалося додати статтю '{news_item.title}' через помилку: {e}")

    print(f"Додано нових статей: {new_articles_count}")

    # Якщо немає нових статей, нічого кластеризувати
    if new_articles_count == 0:
        print("Немає нових статей для кластеризації.")
        return

    # 3. Оновлення кластерів
    print("Оновлення кластерів...")
    unclustered_articles = Article.objects.filter(cluster__isnull=True).order_by('date')
    clusters = list(Cluster.objects.all())

    for article in unclustered_articles:
        # Обчислюємо ембеддинг статті без збереження у БД
        article_embedding = get_embedding(article.title)
        if article_embedding is None:
            # Якщо ембеддінг пустий, пропускаємо цю статтю
            print(f"Пропущено статтю без тексту: {article.title}")
            continue

        best_cluster = None
        best_similarity = -1

        # Знаходимо найбільш схожий кластер
        for cluster in clusters:
            sim = cosine_similarity(article_embedding, cluster.mean_embedding)
            if sim >= similarity_threshold and sim > best_similarity:
                best_similarity = sim
                best_cluster = cluster

        if best_cluster:
            # Інкрементальне оновлення mean_embedding
            current_mean = torch.tensor(best_cluster.mean_embedding)
            new_embedding = torch.tensor(article_embedding)
            updated_mean = (current_mean * cluster.num_articles + new_embedding) / (cluster.num_articles + 1)
            best_cluster.mean_embedding = updated_mean.tolist()
            best_cluster.num_articles += 1
            best_cluster.updated_at = timezone.now()
            best_cluster.save()

            # Прив'язуємо статтю до кластеру
            article.cluster = best_cluster
            article.save()

            print(f"Додано статтю '{article.title}' до кластера {best_cluster.id} зі схожістю {best_similarity:.2f}")
        else:
            # Створюємо новий кластер
            new_cluster = Cluster.objects.create(
                mean_embedding=article_embedding,
                num_articles=1
            )
            clusters.append(new_cluster)  # Додаємо в список для подальших порівнянь

            # Прив'язуємо статтю до нового кластеру
            article.cluster = new_cluster
            article.save()


    print("Процес оновлення кластерів завершено.")


