# Generated by Django 5.1.4 on 2025-01-18 01:19

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="habit",
            name="category",
            field=models.CharField(
                choices=[
                    ("health", "Health"),
                    ("productivity", "Productivity"),
                    ("learning", "Learning"),
                ],
                default="health",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="habit",
            name="name",
            field=models.CharField(
                max_length=100,
                unique=True,
                validators=[django.core.validators.MinLengthValidator(3)],
            ),
        ),
    ]
