# Generated by Django 4.2.2 on 2023-08-16 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0009_alter_useradditional_bust_size_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useradditional',
            name='gender_interested',
            field=models.CharField(choices=[('W', 'Women'), ('M', 'Men')], max_length=10),
        ),
    ]
