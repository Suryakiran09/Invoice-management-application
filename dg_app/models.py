from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models import Sum
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_delete
from django.dispatch import receiver
from dagz_project.custom_azure import AzureMediaStorage

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    host = models.CharField(max_length=255, null=True, blank=True)
    eemail = models.EmailField(null=True, blank=True)
    epassword = models.CharField(max_length=30, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email

class KS61(models.Model):
    Registered_Business_Address = models.JSONField(null=True, blank=True)
    Telephone = models.CharField(max_length=30, null=True, blank=True)
    Email = models.CharField(max_length=30, null=True, blank=True)
    Company_Number = models.CharField(max_length=20, null=True, blank=True)
    Vat_Number = models.CharField(max_length=20, null=True, blank=True)
    Trading_Address = models.JSONField(null=True, blank=True)
    Business_Name = models.CharField(max_length=50, null=True, blank=True)
    Account_Terms = models.CharField(max_length=20, null=True, blank=True)
    Invoice_Date = models.CharField(max_length=20, null=True, blank=True)
    Invoice_Number = models.CharField(max_length=20, null=True, blank=True)
    Date = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateField(default=timezone.now().date())
    Authorisation_Number = models.CharField(max_length=20, null=True, blank=True)
    Make = models.CharField(max_length=50, null=True, blank=True)
    Model = models.CharField(max_length=50, null=True, blank=True)
    Registration = models.JSONField(null=True, blank=True)
    Description_of_Work = models.JSONField(null=True, blank=True)
    Price = models.JSONField(null=True, blank=True)
    Net_Total = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    Vat_at_20_Percent = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    Invoice_Total = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    Total_Payable = models.CharField(max_length=100, null=True, blank=True)
    Payment_Due = models.CharField(max_length=100, null=True, blank=True)
    Customer_Name = models.CharField(max_length=100, null=True, blank=True)
    file = models.OneToOneField('Invoices', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        db_table = 'ks61'
        
    def __str__(self):
        if self.Invoice_Number:
            return self.Invoice_Number
        else:
            return "No value"
    

class Invoices(models.Model):
    STATUS_CHOICES = [
        ('Processed', 'Processed'),
        ('Rejected', 'Rejected'),
    ]
    
    # Custom function to determine the folder path based on status
    def get_upload_path(instance, filename):
        if instance.status == 'Rejected':
            return f'inv_rejected/{filename}'
        else:
            return f'invoices/{filename}'

    invoice = models.FileField(upload_to='invoices')
    date = models.DateField(default=timezone.now().date())
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Processed')
    message = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return self.invoice.name
    
    class Meta:
        ordering = ['-date']
        
class Product(models.Model):
    description = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.description}: {self.price}"


@receiver(post_delete, sender=Invoices)
def delete_file_from_azure(sender, instance, **kwargs):
    file_name = instance.invoice.name
    storage = AzureMediaStorage()
    storage.delete(file_name)