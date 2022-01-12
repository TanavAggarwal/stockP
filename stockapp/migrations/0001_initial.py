# Generated by Django 3.0.5 on 2022-01-10 12:51

from django.db import migrations, models
import djongo.models.fields
import stockapp.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Graphs',
            fields=[
                ('id', models.IntegerField(default=stockapp.models.autoinc, primary_key=True, serialize=False)),
                ('usid', models.IntegerField(default=0)),
                ('g1', models.TextField()),
                ('g2', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Holdings',
            fields=[
                ('id', models.IntegerField(default=stockapp.models.autoinc, primary_key=True, serialize=False)),
                ('usid', models.IntegerField(default=0)),
                ('data', djongo.models.fields.JSONField(default={'avg_price': [], 'ltp': [], 'net_qty': [], 'sector': [], 'symbol': []})),
                ('data2', djongo.models.fields.JSONField(default={'invAmt': [], 'nav': [], 'schemeCd': [], 'schemeId': [], 'units': []})),
            ],
        ),
    ]