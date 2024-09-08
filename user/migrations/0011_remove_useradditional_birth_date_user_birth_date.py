# Generated by Django 4.2.16 on 2024-09-08 07:26

from django.db import migrations, models


def migrate_birth_date(apps, schema_editor):
    UserAdditional = apps.get_model('user', 'UserAdditional')

    for additional in UserAdditional.objects.all():
        user = additional.user
        user.birth_date = additional.birth_date
        user.save()

class Migration(migrations.Migration):

    dependencies = [
        ('user', '0010_alter_useradditional_gender_interested'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='birth_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.RunPython(migrate_birth_date),
        migrations.RemoveField(
            model_name='useradditional',
            name='birth_date',
        ),
    ]
