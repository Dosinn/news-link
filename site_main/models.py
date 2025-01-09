from django.db import models


class Articles(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    date = models.CharField(max_length=255)
    img_url = models.CharField(max_length=255)
    source = models.CharField(max_length=255)

# from djongo import models
# from django.utils import timezone
# # from django.contrib.postgres.fields import JSONField  # якщо потрібно, або використайте models.JSONField


