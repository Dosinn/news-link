from mongoengine import Document, StringField, DateTimeField, IntField, ListField, ReferenceField, connect, FloatField
from datetime import datetime

connect(
    db="NewsLink",
    host="mongodb+srv://dosi:hGUu7HixfbVFYdEU@cluster0.kyhro.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    username="dosi",
    password="hGUu7HixfbVFYdEU",
    authentication_source="admin",
    tls=True
)

MONTHS_UA = {
    1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
    5: "травня", 6: "червня", 7: "липня", 8: "серпня",
    9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
}


class SourceRating(Document):
    meta = {'collection': 'source_rating'}

    source = StringField()
    rating = FloatField(default=0)
    num_rating = IntField(default=0)


class Cluster(Document):
    meta = {'collection': 'clustering_cluster'}

    id = IntField(primary_key=True)
    mean_embedding = ListField(FloatField())
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    num_articles = IntField(default=0)

    @property
    def articles(self):
        return Article.objects(cluster_id=self.id)


class Article(Document):
    meta = {'collection': 'clustering_article'}

    id = IntField(primary_key=True)  # Числовий ID
    slug = StringField(max_length=255)
    url = StringField(max_length=255)
    title = StringField(max_length=255)
    date = DateTimeField()
    img_url = StringField(max_length=255)
    source = StringField(max_length=255)
    views = IntField(default=0)

    cluster_id = IntField()

    def get_formatted_date(self):
        from django.utils.timezone import localtime
        local_date = localtime(self.date)
        MONTHS_UA = {
            1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
            5: "травня", 6: "червня", 7: "липня", 8: "серпня",
            9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
        }
        return local_date.strftime(f"%H:%M, %d {MONTHS_UA[local_date.month]} %Y")



# from djongo import models
# from django.utils import timezone
# from django.utils.formats import date_format
# from django.utils.timezone import localtime
#
# MONTHS_UA = {
#     1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
#     5: "травня", 6: "червня", 7: "липня", 8: "серпня",
#     9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
# }
#
#
# class Cluster(models.Model):
#     id = models.AutoField(primary_key=True)
#     mean_embedding = models.JSONField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     num_articles = models.IntegerField(default=0)
#
#
# class Article(models.Model):
#     id = models.IntegerField(primary_key=True)
#     slug = models.CharField(max_length=255, unique=True)
#     url = models.CharField(max_length=255, unique=True)
#     title = models.CharField(max_length=255)
#     date = models.DateTimeField()
#     img_url = models.CharField(max_length=255)
#     source = models.CharField(max_length=255)
#     views = models.IntegerField(default=0)
#
#     cluster = models.ForeignKey(Cluster, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
#
#     def to_dict(self):
#         return {
#             'img_url': self.img_url,
#             'id': self.id,
#             'title': self.title,
#             'date': self.date,  # Вивід у бажаному форматі
#             'source': self.source,
#             'views': self.views
#         }
#
#     def get_formatted_date(self):
#         """
#         Форматує дату у вигляді: 15:18, 02 січня 2025 (локальний час)
#         """
#         local_date = localtime(self.date)  # Перетворення на локальний час
#         return local_date.strftime(f"%H:%M, %d {MONTHS_UA[local_date.month]} %Y")
