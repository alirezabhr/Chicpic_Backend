# Generated by Django 4.2.2 on 2023-11-15 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clothing', '0010_alter_category_options_category_priority'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='original_id',
            field=models.BigIntegerField(null=True, unique=True),
        ),
        migrations.AddField(
            model_name='variant',
            name='original_id',
            field=models.BigIntegerField(null=True, unique=True),
        ),
    ]
