# Generated by Django 4.2.7 on 2024-03-15 14:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dg_app', '0006_invoices_date_invoices_status_alter_ks61_created_at'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='invoices',
            options={'ordering': ['-date']},
        ),
    ]
