# Generated by Django 4.2.7 on 2024-03-15 14:24

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dg_app', '0005_alter_ks61_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoices',
            name='date',
            field=models.DateField(auto_now=True),
        ),
        migrations.AddField(
            model_name='invoices',
            name='status',
            field=models.CharField(choices=[('Processed', 'Processed'), ('Rejected', 'Rejected')], default='Processed', max_length=10),
        ),
        migrations.AlterField(
            model_name='ks61',
            name='created_at',
            field=models.DateField(default=datetime.date(2024, 3, 15), editable=False),
        ),
    ]
