from djongo import models
from django.utils import timezone
from django.contrib.postgres.fields import JSONField  # якщо потрібно, або використайте models.JSONField
from django.utils.formats import date_format
from django.utils.timezone import localtime

MONTHS_UA = {
    1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
    5: "травня", 6: "червня", 7: "липня", 8: "серпня",
    9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
}


class Cluster(models.Model):
    id = models.AutoField(primary_key=True)
    mean_embedding = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    num_articles = models.IntegerField(default=0)


class Article(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    date = models.DateTimeField()
    img_url = models.CharField(max_length=255)
    source = models.CharField(max_length=255)
    views = models.IntegerField(default=0)

    cluster = models.ForeignKey(Cluster, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')

    def to_dict(self):
        return {
            'img_url': self.img_url,
            'id': self.id,
            'title': self.title,
            'date': self.date,  # Вивід у бажаному форматі
            'source': self.source,
            'views': self.views
        }

    def get_formatted_date(self):
        """
        Форматує дату у вигляді: 15:18, 02 січня 2025 (локальний час)
        """
        local_date = localtime(self.date)  # Перетворення на локальний час
        return local_date.strftime(f"%H:%M, %d {MONTHS_UA[local_date.month]} %Y")