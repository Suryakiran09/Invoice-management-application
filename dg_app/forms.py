from django import forms
from .models import Invoices

class InvoicesForm(forms.ModelForm):
    class Meta:
        model = Invoices
        fields = ["invoice"]