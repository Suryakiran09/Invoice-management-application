# Generated by Django 4.2.7 on 2024-03-08 09:02

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('dg_app', '0003_ks61_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ks61',
            name='created_at',
            field=models.DateField(default=django.utils.timezone.now, editable=False),
        ),
    ]