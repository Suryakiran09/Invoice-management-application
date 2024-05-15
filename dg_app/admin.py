from django.contrib import admin
from .models import CustomUser, KS61, Invoices, Product

# Register your models here.

admin.site.register(CustomUser)
admin.site.register(KS61)
admin.site.register(Invoices)
admin.site.register(Product)