# Generated by Django 4.1.7 on 2023-05-04 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0017_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='marked',
            field=models.BooleanField(default=False),
        ),
    ]
