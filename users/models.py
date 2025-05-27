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


class UserRecommendation(Document):
    meta = {'collection': 'users_recommendation'}

    user_id = IntField(primary_key=True)
    embedding = ListField(FloatField())
    views_count = IntField(default=1)
    viewed_id = ListField(IntField())
