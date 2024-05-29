# Generated by Django 4.1.7 on 2023-05-10 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0023_remove_product_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='discount_percent',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='order',
            name='promo_code',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]