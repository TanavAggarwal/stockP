# from django.db import models
from djongo import models
from django import forms

# Create your models here.


def autoinc():
    largest = Holdings.objects.all().order_by('id').last()
    if not largest:
        return 1
    return largest.id + 1


class Holdings(models.Model):
    id = models.IntegerField(primary_key=True, default=autoinc)
    usid = models.IntegerField(default=0)
    data = models.JSONField(
        default={'symbol': [], 'net_qty': [], 'avg_price': [], 'ltp': [], 'sector': []})
    data2 = models.JSONField(
        default={'schemeId': [], 'invAmt': [], 'units': [], 'nav': [], 'schemeCd': []})


class Graphs(models.Model):
    id = models.IntegerField(primary_key=True, default=autoinc)
    usid = models.IntegerField(default=0)
    g1 = models.TextField()
    g2 = models.TextField()
