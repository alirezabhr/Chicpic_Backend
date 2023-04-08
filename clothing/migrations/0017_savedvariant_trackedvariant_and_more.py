# Generated by Django 4.1.6 on 2023-04-08 09:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clothing', '0016_shop_website'),
    ]

    operations = [
        migrations.CreateModel(
            name='SavedVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('saved_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TrackedVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tracked_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='trackedproduct',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='trackedproduct',
            name='product',
        ),
        migrations.RemoveField(
            model_name='trackedproduct',
            name='user',
        ),
        migrations.AlterModelOptions(
            name='variant',
            options={'ordering': ('id',)},
        ),
        migrations.DeleteModel(
            name='SavedProduct',
        ),
        migrations.DeleteModel(
            name='TrackedProduct',
        ),
        migrations.AddField(
            model_name='trackedvariant',
            name='variant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='clothing.variant'),
        ),
        migrations.AddField(
            model_name='savedvariant',
            name='variant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='clothing.variant'),
        ),
        migrations.AlterUniqueTogether(
            name='trackedvariant',
            unique_together={('user', 'variant')},
        ),
        migrations.AlterUniqueTogether(
            name='savedvariant',
            unique_together={('user', 'variant')},
        ),
    ]
