# Generated by Django 4.2.7 on 2024-04-16 11:16

import datetime
import dg_app.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dg_app', '0014_alter_invoices_date_alter_ks61_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoices',
            name='date',
            field=models.DateField(default=datetime.date(2024, 4, 16)),
        ),
        migrations.AlterField(
            model_name='invoices',
            name='invoice',
            field=models.FileField(upload_to=dg_app.models.Invoices.get_upload_path),
        ),
        migrations.AlterField(
            model_name='ks61',
            name='created_at',
            field=models.DateField(default=datetime.date(2024, 4, 16)),
        ),
    ]