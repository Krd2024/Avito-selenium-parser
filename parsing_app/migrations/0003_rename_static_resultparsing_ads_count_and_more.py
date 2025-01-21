# Generated by Django 5.1.5 on 2025-01-21 10:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parsing_app', '0002_requestuser_resultparsing'),
    ]

    operations = [
        migrations.RenameField(
            model_name='resultparsing',
            old_name='static',
            new_name='ads_count',
        ),
        migrations.RenameField(
            model_name='resultparsing',
            old_name='created_ad',
            new_name='checked_at',
        ),
        migrations.AddField(
            model_name='resultparsing',
            name='request',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='result_parsing', to='parsing_app.requestuser'),
            preserve_default=False,
        ),
    ]
