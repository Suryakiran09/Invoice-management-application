# Generated by Django 4.2.7 on 2024-03-15 20:01

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dg_app', '0007_alter_invoices_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoices',
            name='date',
            field=models.DateField(default=datetime.date(2024, 3, 15), editable=False),
        ),
    ]
