# Generated by Django 4.2.16 on 2024-09-27 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clothing', '0015_shop_deleted_at_shop_is_deleted'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='deleted_at',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='is_deleted',
            field=models.BooleanField(default=False, editable=False),
        ),
    ]
