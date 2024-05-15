# Generated by Django 4.2.7 on 2024-04-21 00:28

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dg_app', '0017_alter_invoices_date_alter_ks61_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoices',
            name='message',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='invoices',
            name='date',
            field=models.DateField(default=datetime.date(2024, 4, 21)),
        ),
        migrations.AlterField(
            model_name='invoices',
            name='invoice',
            field=models.FileField(upload_to='invoices'),
        ),
        migrations.AlterField(
            model_name='ks61',
            name='created_at',
            field=models.DateField(default=datetime.date(2024, 4, 21)),
        ),
    ]
