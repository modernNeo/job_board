# Generated by Django 4.2.3 on 2023-10-13 06:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0024_alter_joblocation_job_board'),
    ]

    operations = [
        migrations.AddField(
            model_name='joblocation',
            name='easy_apply',
            field=models.BooleanField(default=None, null=True),
        ),
    ]
