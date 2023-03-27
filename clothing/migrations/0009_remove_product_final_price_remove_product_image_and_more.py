# Generated by Django 4.1.6 on 2023-03-27 14:31

import clothing.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clothing', '0008_product_brand'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='final_price',
        ),
        migrations.RemoveField(
            model_name='product',
            name='image',
        ),
        migrations.RemoveField(
            model_name='product',
            name='is_deleted',
        ),
        migrations.RemoveField(
            model_name='product',
            name='link',
        ),
        migrations.RemoveField(
            model_name='product',
            name='original_price',
        ),
        migrations.CreateModel(
            name='Variant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=clothing.models.product_image_upload_path)),
                ('link', models.URLField(max_length=256)),
                ('original_price', models.DecimalField(decimal_places=2, max_digits=5)),
                ('final_price', models.DecimalField(decimal_places=2, max_digits=5)),
                ('is_available', models.BooleanField()),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='clothing.product')),
            ],
        ),
        migrations.CreateModel(
            name='SizeGuide',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('option', models.CharField(choices=[('Bust', 'Bust'), ('Waist', 'Waist'), ('Inseam', 'Inseam'), ('Hips', 'Hips'), ('Shoulder', 'Shoulder'), ('Chest', 'Chest'), ('Height', 'Height')], max_length=20)),
                ('value', models.PositiveSmallIntegerField()),
                ('variant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='size_guides', to='clothing.variant')),
            ],
            options={
                'unique_together': {('variant', 'option')},
            },
        ),
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attribute', models.CharField(choices=[('Color', 'Color'), ('Size', 'Size'), ('Length', 'Length')], max_length=15)),
                ('value', models.CharField(max_length=15)),
                ('variant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attributes', to='clothing.variant')),
            ],
            options={
                'unique_together': {('variant', 'attribute')},
            },
        ),
    ]
