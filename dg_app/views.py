from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, get_user_model
from django.http import HttpResponse
import psycopg2
import subprocess
import pandas as pd
from .models import KS61, Invoices, Product
from .forms import InvoicesForm
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
import plotly.express as px
import plotly.graph_objects as go
import plotly.offline as pyo
import seaborn as sns
import matplotlib.pyplot as plt
from django.db.models import Count, Sum, Min, Max
from decimal import Decimal
from . import utils
from django.views.decorators.csrf import csrf_protect
from django.core.files.storage import default_storage
from .dashboard_plots import generate_invoice_total_pie_chart_for_dashboard, generate_invoice_total_over_time_chart, generate_invoice_distribution_by_business_name, generate_top_invoices_chart,\
    generate_invoice_value_vs_net_total_scatter, generate_invoices_per_make_donut_chart
from .models import CustomUser
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import PyPDF2, re, psycopg2, pdfplumber, tabula, os, json, csv, codecs, io
from django.conf import settings
from django.core.mail import EmailMessage, get_connection
import socket
import ssl
from smtplib import SMTP
from email.message import EmailMessage
import smtplib

CustomUser = get_user_model()



def register_user(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Validate if the email is unique
        if CustomUser.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error': 'Email is already registered'})

        # Create a user
        user = CustomUser.objects.create_user(email=email, password=password)
        user.name = name
        user.save()

        # Log in the user
        user = authenticate(request, email=email, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')

    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            error = 'Invalid login credentials. Please try again.'
            return render(request, 'login.html', {'error': error})

    return render(request, 'login.html')

@login_required(login_url='login')
def dashboard(request):
    
    min_date = KS61.objects.all().aggregate(min_date=Min('created_at'))['min_date']
    max_date = KS61.objects.all().aggregate(max_date=Max('created_at'))['max_date']
    
    
    
    if min_date and max_date != None :
        start_date = request.GET.get('start_date',str(min_date))
        end_date = request.GET.get('end_date',str(max_date))
        
    invoices = Invoices.objects.all()
    values = KS61.objects.all()
    
    print(start_date, end_date)

    if start_date or end_date:
        # If both start_date and end_date are provided, filter invoices by date range
        invoices = invoices.filter(date__range=[start_date, end_date])
        values = values.filter(created_at__range=[start_date, end_date])
    
    processed_invoices_count = invoices.filter(status='Processed').count()
    rejected_invoices_count = invoices.filter(status='Rejected').count()
    invoices_sum = round(values.aggregate(total_sum=Sum('Invoice_Total'))['total_sum'] or 0, 2)
    unique_makes_count = values.values('Make').distinct().count()
    
    chart_html = generate_invoice_total_pie_chart_for_dashboard(values)
    top_invoices = generate_invoice_total_over_time_chart(values)
    invoice_distribution = generate_top_invoices_chart(values)
    invoice_value = generate_invoice_value_vs_net_total_scatter(values)
    invoices_per_make = generate_invoices_per_make_donut_chart(values)
    
    context = {
        "processed_invoices_count": processed_invoices_count,
        "rejected_invoices_count": rejected_invoices_count,
        "invoices_sum": invoices_sum,
        "unique_makes_count": unique_makes_count,
        "fig1" : chart_html,
        "fig2" : top_invoices,
        "fig3" : invoice_distribution,
        "fig4" : invoice_value,
        "fig5" : invoices_per_make,
        "start_date": str(start_date),
        "end_date": str(end_date),
    }
    
    return render(request, 'dashboard.html', context)


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
@login_required(login_url='login')
def pdf_view(request, invoice_id=None):
    status = request.GET.get('status', 'Processed')  # Default value is 'Processed'
    pdf = request.GET.get('pdf', None)
    
    inv =  Invoices.objects.all()
    
    min_date = Invoices.objects.all().aggregate(min_date=Min('date'))['min_date']
    max_date = Invoices.objects.all().aggregate(max_date=Max('date'))['max_date']
    
    start_date = request.GET.get('start_date',str(min_date))
    end_date = request.GET.get('end_date',str(max_date))
    
    if status == 'Processed':
        invoices = Invoices.objects.filter(status='Processed')
    elif status == 'Rejected':
        invoices = Invoices.objects.filter(status='Rejected')
    else:
        invoices = Invoices.objects.all()
        
    print(start_date,end_date)
    if start_date or end_date:
        invoices = invoices.filter(date__range=[start_date, end_date])
        
    print(pdf)
    
    if pdf:
        invoices = invoices.filter(invoice__icontains = pdf)
        print(invoices)
    
    if invoice_id:
        selected_invoice = invoices.get(id=invoice_id)
    else:
        selected_invoice = invoices.first()
        
        
    message = selected_invoice.message
    print(message)
    paginator = Paginator(invoices, 10)  # Show 10 invoices per page

    page_number = request.GET.get('page', 1)  # Default to page 1 if page number is not provided or invalid
    try:
        page_number = int(page_number)
    except ValueError:
        page_number = 1

    try:
        invoices = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        invoices = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        invoices = paginator.page(paginator.num_pages)
    
    context = {
        'invoices': invoices,
        'selected_invoice': selected_invoice,
        'status': status,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "inv":inv,
        "message": message
    }


    return render(request, 'pdfview.html', context)

@login_required(login_url='login')
def invoice_data(request):
    # Initial values for start_date and end_date
    min_date = Invoices.objects.all().aggregate(min_date=Min('date'))['min_date']
    max_date = Invoices.objects.all().aggregate(max_date=Max('date'))['max_date']
    
    if not max_date:
        max_date = min_date
        
    start_date = min_date
    end_date = max_date
    
    customer_name = request.GET.get('customer_name', None)
    
    vendor = request.GET.get('vendor', None)
    # Get data based on the selected date range
    
    print("Customer type: " + str(type(customer_name)))
    print("Vendor type: " + str(type(vendor)))
    
    start_date = request.GET.get('start_date',str(start_date))
    end_date = request.GET.get('end_date', str(end_date))
        
    # Fetch the data for invoices
    invoices = KS61.objects.filter(created_at__range=[start_date, end_date])
    

    if customer_name and customer_name!="None":
        invoices = invoices.filter(Customer_Name=customer_name)
        
    if vendor and vendor!="None":
        invoices = invoices.filter(Make__icontains=vendor)
    
    customers = invoices.order_by().values('Customer_Name').distinct()
    
    customers = list(customers)
    
    vendors =  invoices.order_by().values('Make').distinct()
    
    # Calculate the total value of invoices
    total_invoice = round(invoices.aggregate(total_invoice=Sum('Invoice_Total'))['total_invoice'] or 0, 2)
    
    # Prepare context for rendering
    context = {
        'start_date': str(start_date),
        'end_date': str(end_date),
        'min_date': str(min_date),
        'invoices': invoices,
        'total_invoice': total_invoice,
        'customers' : customers,
        'vendors' : vendors
    }
    
    return render(request, 'invoice_data.html', context)



@login_required(login_url='login')
def user_profile(request):
    user = request.user

    if request.method == 'POST' and "host" not in request.POST:
        # Update user information based on the submitted form data
        user.name = request.POST.get('name')
        user.email = request.POST.get('email')
        
        password = request.POST.get('password')
        if password:
            user.set_password(password)
            update_session_auth_hash(request, user)

        user.save()
        status = "User details updated"
        return render(request, 'user_profile.html', {'status': status})
    
    elif request.method == "POST" and "host" in request.POST:
        print("Came into this method")
        host = request.POST.get('host')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        CustomUser.objects.filter(pk=request.user.pk).update(
            host=host,
            eemail=email,
            epassword=password
        )
        status = "Additional details updated"
        return render(request, 'user_profile.html', {'status': status})
    
    return render(request, 'user_profile.html')

@login_required(login_url='login')
def file_upload(request):
    error_message = "Not Running"  # Initialize error_message

    if request.method == 'POST':
        form = InvoicesForm(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = request.FILES['invoice']

            try:
                # Call data_extractor method here before saving the form
                data = utils.data_extractor(uploaded_file, form)
                
                if data["success"]==False:
                    error_message = data['message']
                    return render(request, 'file_upload.html', {'form': form, 'message': error_message})
                elif data["success"]==True:
                    error_message = "success"
                    return render(request, 'file_upload.html', {'form': form, 'message': error_message})
            except Exception as e:
                # If an error occurs during data extraction, set error_message
                error_message = f"Error during data extraction: {str(e)}"
        else:
            error_message = "Form is not valid"

    form = InvoicesForm()
    return render(request, 'file_upload.html', {'form': form, 'message': error_message})

def direct_data_extractor(request, id):
    response = utils.direct_data_extractor(request, id)
    
    return redirect(reverse('pdf_view'))

def discard_invoice(request, id):
    if request.method == 'POST':
        invoice = Invoices.objects.get(pk=id)
        email = request.POST['email']
        comment = request.POST['message']
        subject = f"Discarded Invoice - {invoice.invoice.name}"
        message = f"The invoice '{invoice.invoice.name}' has been discarded.\nComment: {comment}\nError message: {invoice.message}\n\nRegards,\nDataGridz Support Team."
        
        msg = EmailMessage()
        
        msg.set_content(message)
        
        msg['Subject'] = subject
        msg['From'] = request.user.eemail
        msg['To'] = email
        
        server = smtplib.SMTP_SSL(request.user.host, 465)
        

        try:
            server.login(request.user.eemail, request.user.epassword)
            server.send_message(msg)
            server.quit()
            invoice.delete()
            return redirect('dashboard')
        except Exception as e:
            # Handle the exception or log it
            print(f"Error sending email: {e}")
            return redirect('dashboard')  # Redirect or display error message to the user