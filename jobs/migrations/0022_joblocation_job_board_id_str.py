# Generated by Django 4.2.3 on 2023-10-07 09:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0021_rename_linkedin_id_joblocation_job_board_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='joblocation',
            name='job_board_id_str',
            field=models.CharField(default=None, max_length=500),
        ),
    ]
