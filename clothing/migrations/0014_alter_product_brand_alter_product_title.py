# Generated by Django 4.2.2 on 2024-01-21 13:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clothing', '0013_alter_variant_final_price_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='brand',
            field=models.CharField(max_length=60),
        ),
        migrations.AlterField(
            model_name='product',
            name='title',
            field=models.CharField(max_length=200),
        ),
    ]
