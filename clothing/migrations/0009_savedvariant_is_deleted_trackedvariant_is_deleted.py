# Generated by Django 4.2.2 on 2023-08-10 11:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clothing', '0008_alter_trackedvariant_tracked_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='savedvariant',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='trackedvariant',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
