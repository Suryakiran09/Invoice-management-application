from .views import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, get_user_model
from django.http import HttpResponse
import psycopg2
import subprocess
import pandas as pd
from .models import KS61, Invoices, Product
from .forms import InvoicesForm
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
from .forms import *
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


import logging

logging.basicConfig(filename='file_rejections.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def data_extractor(file, form_data):
    try:
        pdf_file_path = file  # Assuming file is already handled correctly
        
        
        
        with pdfplumber.open(pdf_file_path) as pdf:
            pdf_text = ""
            for page in pdf.pages:
                pdf_text += page.extract_text()
                page = pdf.pages[0]
                table = page.extract_table()
                
            table_data = []
            for row in table:
                # Remove leading and trailing spaces from each column name
                cleaned_row = [column.strip() if isinstance(column, str) else column for column in row]
                table_data.append(cleaned_row)
        
        
        
        Telephone_Pattern = r"Telephone:\s+?(\d.*)"
        Email_Pattern = r"Email:\s+?(\w.+)"
        Company_Number_Pattern = r"Company\s+Number:\s+?(\d.+)"
        VAT_Pattern = r"VAT\s+Number:\s+(\d.*)"
        Business_Name_Pattern = r"Business\s+Name:\s+?(\w.*)"
        Account_Terms_Pattern = r"Account\s+Terms:\s+?(\w.*)"
        Invoice_Date_Pattern = r"Invoice\s+Date:\s+?(\w.*)"
        Invoice_Number_Pattern = r"Invoice\s+Number:\s+?(\w.*)"

        NET_TOTAL_Pattern = r"NET\s+TOTAL:\s+?(\w.*)"

        elephone = []
        Email = []
        Company_Number = []
        VAT_Number = []
        Business_Name = []
        Account_Terms = []
        Invoice_Date = []
        Invoice_Number = []
        Total_payable = []
        NET_TOTAL = []

        text = page.extract_text()
        Telephone = re.search(Telephone_Pattern, text, re.IGNORECASE)
        Email = re.search(Email_Pattern, text, re.IGNORECASE)
        Company_Number = re.search(Company_Number_Pattern, text)
        VAT_Number =   re.search(VAT_Pattern, text)
        Business_Name = re.search(Business_Name_Pattern, text, re.IGNORECASE)
        Account_Terms = re.search(Account_Terms_Pattern, text, re.IGNORECASE)
        Invoice_Date = re.search(Invoice_Date_Pattern, text)
        Invoice_Number = re.search(Invoice_Number_Pattern, text, re.IGNORECASE)

        # if Telephone:
        #     print(f"Telephone: {Telephone.group(1)}")
        # if Email:
        #     print(f"Email: {Email.group(1)}")
        # if Company_Number:
        #     print(f"Company_Number: {Company_Number.group(1)}")
        # if VAT_Number:
        #     print(f"VAT_Number: {VAT_Number.group(1)}")
        # if Business_Name:
        #     print(f"Business_Name: {Business_Name.group(1)}")
        # if Account_Terms:
        #     print(f"Account_Terms: {Account_Terms.group(1)}")
        # if Invoice_Date:
        #     print(f"Invoice_Date: {Invoice_Date.group(1)}")
        # if Invoice_Number:
        #     print(f"Invoice_Number: {Invoice_Number.group(1)}")
        
        
        NET_pattern = r"NET\s+TOTAL:(.*)"
        vat_pattern = r"VAT\s+@\s+20%:(.*)"
        invoice_total_pattern = r"INVOICE\s+TOTAL:(.*)"
        total_payable_pattern = r"Total\s(\w.*)"
        payment_due_pattern = r"Payment\s(\w.*)"

        match1 = re.search(NET_pattern, pdf_text)
        match2 = re.search(vat_pattern, pdf_text)
        match3 = re.search(invoice_total_pattern, pdf_text)
        match4 = re.search(total_payable_pattern, pdf_text)
        match5 = re.search(payment_due_pattern, pdf_text)

        if match1:
            NET_value = match1.group(1)
            # print(f"NET TOTAL: {NET_value}")
        if match2:
            vat_value = match2.group(1)
            # print(f"VAT: {vat_value}")
        if match3:
            invoice_total_value = match3.group(1)
            # print(f"INVOICE TOTAL: {invoice_total_value}")
        if match4:
            total_payable = match4.group(1)
            # print(f"TOTAL PAYABLE: {total_payable}")
        if match5:
            payment_due = match5.group(1)
            # print(f"Payment due: {payment_due}")
            
        # These coordinates should define a rectangular region that includes the entire table.
        areas = [
        [60, 200, 120, 400],
        [60, 400, 120, 600],
        [440, 80, 550, 650],
        ]
        tables = tabula.read_pdf(pdf_file_path, pages='1', area=areas)

        table1 = tabula.read_pdf(pdf_file_path, pages=1, area=[45, 200, 120, 440])[0]
        #table2 = tabula.read_pdf(pdf_file_path, pages=1, area=[47, 400, 120, 600])[0]
        table2 = tabula.read_pdf(pdf_file_path, pages=1, area=[44, 480, 120, 600])[0]
        #print(table1)
        #print(table2)

        #Vehicle Details Table
        table3 = tabula.read_pdf(pdf_file_path, pages=1, area=[420, 70, 550, 140])[0]
        table11 = tabula.read_pdf(pdf_file_path, pages=1, area=[430, 140, 550, 200])[0] #CUSTOMER_NAME Column
        table4 = tabula.read_pdf(pdf_file_path, pages=1, area=[410, 190, 540, 290])[0]
        table5 = tabula.read_pdf(pdf_file_path, pages=1, area=[400, 290, 470, 340])[0]

        table6 = tabula.read_pdf(pdf_file_path, pages=1, area=[410, 290, 550, 340])[0]
        table7 = tabula.read_pdf(pdf_file_path, pages=1, area=[420, 332, 530, 375])[0]
        table8 = tabula.read_pdf(pdf_file_path, pages=1, area=[420, 390, 550, 440],guess=True)[0]
        table9 = tabula.read_pdf(pdf_file_path, pages=1, area=[435, 450, 550, 530])[0] #done
        table10 = tabula.read_pdf(pdf_file_path, pages=1, area=[430, 520, 510, 580])[0] #done

        values_in_column1 = []
        values_in_column2 = []

        values_in_column3 = []
        values_in_column4 = []
        values_in_column5 = []
        values_in_column6 = []
        values_in_column7 = []
        values_in_column8 = []
        values_in_column9 = []
        values_in_column10 = []
        values_in_column11 = []
        
        
        for _, row in table1.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column1 = row.iloc[0]
            values_in_column1.append(value_in_column1)

        for _, row in table2.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column2 = row.iloc[0]
            values_in_column2.append(value_in_column2)

        for _, row in table3.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column3 = row.iloc[0]
        #value_in_column3 = row.iloc[1]
            values_in_column3.append(value_in_column3)

        for _, row in table4.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column4 = row.iloc[0]
        #value_in_column3 = row.iloc[1]
            values_in_column4.append(value_in_column4)

        for _, row in table5.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column5 = row.iloc[0]
        #value_in_column3 = row.iloc[1]
            values_in_column5.append(value_in_column5)

        for _, row in table6.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column6 = row.iloc[0]
        #value_in_column3 = row.iloc[1]
            values_in_column6.append(value_in_column6)

        for _, row in table7.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column7 = row.iloc[0]
        #value_in_column3 = row.iloc[1]
            values_in_column7.append(value_in_column7)

        for _, row in table8.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column8 = row.iloc[0]
        #value_in_column3 = row.iloc[1]
            values_in_column8.append(value_in_column8)

        print(values_in_column8)

        for _, row in table9.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column9 = row.iloc[0]
        #value_in_column3 = row.iloc[1]
            values_in_column9.append(value_in_column9)

        for _, row in table10.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column10 = row.iloc[0]
        #value_in_column3 = row.iloc[1]
            values_in_column10.append(value_in_column10)

        for _, row in table11.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column11 = row.iloc[0]
        #value_in_column11 = row.iloc[1]
            values_in_column11.append(value_in_column11)

        # combined_values1 = ', '.join(values_in_column1)  # Join the values with a delimiter
        # combined_values1 = combined_values1.replace(', ', '<br>')
        
        # combined_values2 = ', '.join(values_in_column2)
        # combined_values2 = combined_values2.replace(', ', '<br>')
        # combined_values8 = ",  ".join(values_in_column8)
        # combined_values8 = combined_values8.replace(', ', '<br>')
        # combined_values9 = ",  ".join(values_in_column9)
        # combined_values9 = combined_values9.replace(', ', '<br>')

        #print(combined_values8)
        #print(values_in_column10)
        combined_values10 = [f'{value:.2f}' for value in values_in_column10] # adding two leading zeroes because python during conversion removes it
        # combined_values10 = ",  ".join(combined_values10)
        #combined_values9 = ', '.join(str(val) for val in values_in_column9) #CONVERSION DUE TO INT VALUE, JOIN DOES NOT WORK FOR INT
        # combined_values10 = combined_values10.replace(', ', '<br>')
        
        combined_values1 = json.dumps(values_in_column1)
        combined_values2 = json.dumps(values_in_column2)
        combined_values8 = json.dumps(values_in_column8)
        combined_values9 = json.dumps(values_in_column9)
        combined_values10 = json.dumps(combined_values10)
        
        NET_value = float(NET_value[2:])
        vat_value = float(vat_value[2:])
        invoice_total_value = float(invoice_total_value[2:])
        
        attribute_dict = {
            "Registered Business Address": combined_values1,
            "Telephone": Telephone.group(1),
            "Email": Email.group(1),
            "Company Number": Company_Number.group(1),
            "VAT Number": VAT_Number.group(1),
            "Trading Address": combined_values2,
            "Business Name": Business_Name.group(1),
            "Account Terms": Account_Terms.group(1),
            "Invoice Date": Invoice_Date.group(1),
            "Invoice Number": Invoice_Number.group(1),
            "Date": value_in_column3,
            "Customer Name": value_in_column11,
            "Authorisation Number": value_in_column4,
            "Make": value_in_column6,
            "Model": value_in_column7,
            "Registration": combined_values8,
            "Description of Work": combined_values9,
            "Price": combined_values10,
            "Net Total": NET_value,
            "VAT at 20 Percent": vat_value,
            "Invoice Total": invoice_total_value,
            "Total Payable": total_payable,
            "Payment Due": payment_due,
        }
        
        if not(attribute_dict.get("Registration") and attribute_dict.get("Authorisation Number") and attribute_dict.get("Make")):
            error_message = f"File {file} rejected: Registration, Authorisation Number, and Make are not present in the file."
            
            logging.info(error_message)
            
            return {
            'success': False,
            'message': f"The file '{file}' has been rejected. Error message: {error_message}",
        }
            
        status, message = validate(attribute_dict)
        
        if not status:
            error_message = f"File {file} rejected: {message}"
            
            logging.info(error_message)
            
            invoice_instance = form_data.save(commit=False)
            invoice_instance.status = "Rejected"
            invoice_instance.message = error_message
            invoice_instance.save()
            
            print(invoice_instance)
            
            return {
            'success': False,
            'message': f"The file '{file}' has been rejected. Error message: {error_message}",
        }
        
        invoice_instance = form_data.save(commit=False)
        
        ks61_instance = KS61(
        Registered_Business_Address=combined_values1,
        Telephone=Telephone.group(1),
        Email=Email.group(1),
        Company_Number=Company_Number.group(1),
        Vat_Number=VAT_Number.group(1),
        Trading_Address=combined_values2,
        Business_Name=Business_Name.group(1),
        Account_Terms=Account_Terms.group(1),
        Invoice_Date=Invoice_Date.group(1),
        Invoice_Number=Invoice_Number.group(1),
        Date=value_in_column3,
        Customer_Name=value_in_column11,
        Authorisation_Number=value_in_column4,
        Make=value_in_column6,
        Model=value_in_column7,
        Registration=combined_values8,
        Description_of_Work=combined_values9,
        Price=combined_values10,
        Net_Total=NET_value,
        Vat_at_20_Percent=vat_value,
        Invoice_Total=invoice_total_value,
        Total_Payable='Total ' + total_payable,
        Payment_Due='Payment ' + payment_due,
        file=invoice_instance,
        )
        
        invoice_instance.save()
        
        
        print(ks61_instance.created_at)
        print(ks61_instance)
        ks61_instance.save()
        
        message = f"File {file} Accepted."
            
        logging.info(message)
    
                
        return {
            'success': True,
            'message': 'Data extraction successful',
            'pdf_text': pdf_text,  # You can include additional extracted data if needed
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error during data extraction: {str(e)}',
        }
        
def validate(invoice_data):
    descriptions = eval(invoice_data["Description of Work"])
    prices = list(map(Decimal, eval(invoice_data["Price"])))
    message = ""
    error_message = "None"
    
    pde = False
    item_price_discrepancy = False
    total_price_discrepancy = False
    
    sum_of_prices = Decimal("0.00")
    
    for description, price in zip(descriptions[1:], prices):
        product = Product.objects.filter(description__iexact=description).first()
        
        if not product:
            error_message = f"Product: {description} not found"
            pde = True
            return False, error_message
        
        if price > product.price:
            error_message  = f"Product: {description} has incorrect price"
            item_price_discrepancy = True
            return False, error_message    
        
        sum_of_prices += price
        
    net_total = Decimal(invoice_data["Net Total"])
    
    if sum_of_prices != net_total:
        total_price_discrepancy = True
        error_message  = f"Total price has some discrepancy. Total price: {sum_of_prices}, Net Total: {net_total}"
        return False, error_message
    
    return True, "Success"

def upload_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if csv_file:
            try:
                csv_file_text = csv_file.read().decode('utf-8-sig')
            except UnicodeDecodeError:
                csv_file_text = csv_file.read().decode('iso-8859-1')

            csv_file_io = io.StringIO(csv_file_text)
            reader = csv.reader(csv_file_io)
            headers = next(reader)

            # Initialize mapping with None values
            mapping = {header: None for header in headers}

            # Update mapping with user-selected fields
            for header in headers:
                mapping[header] = request.POST.get(f'map_{header}')
                print(f"Mapping for '{header}': {mapping[header]}")

            objects = []
            for row in reader:
                data = {
                    mapping[header]: row[i]
                    for i, header in enumerate(headers)
                    if mapping[header]  # Only include mapped fields
                }
                obj = KS61(**data)
                objects.append(obj)

            KS61.objects.bulk_create(objects)
            return redirect('home')
    else:
        model_fields = [field.name for field in KS61._meta.get_fields()]
        model_fields = [field for field in model_fields if field not in ['id', 'file', 'created_at']]
        headers = []

    model_fields_json = json.dumps(model_fields)
    return render(request, 'upload_csv.html', {'headers': headers, 'model_fields_json': model_fields_json})


def download_csv(request, queryset):
    opts = queryset.model._meta
    model = queryset.model
    response = HttpResponse()
    # force download.
    response['Content-Disposition'] = 'attachment;filename=export.csv'
    # the csv writer
    writer = csv.writer(response)
    field_names = [field.name for field in opts.fields]
    # Write a first row with header information
    writer.writerow(field_names)
    # Write data rows
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in field_names])
    return response

def export_csv(request):
  # Create the HttpResponse object with the appropriate CSV header.
  data = download_csv(request=request, queryset=KS61.objects.all())
  response = HttpResponse(data, content_type='text/csv')
  return response

def direct_data_extractor(request, id):
    invoice = Invoices.objects.get(pk=id)
    file = invoice.invoice.file
    
    logging.info(f"Starting data extraction for file: {file}")
    
    try:
        pdf_file_path = file  # Assuming file is already handled correctly
        print("File is grabed")
        print(pdf_file_path)
        
        
        with pdfplumber.open(pdf_file_path) as pdf:
            print("pdf is opened")
            pdf_text = ""
            for page in pdf.pages:
                pdf_text += page.extract_text()
                print(pdf_text)
                page = pdf.pages[0]
                table = page.extract_table()
                
            table_data = []
            for row in table:
                # Remove leading and trailing spaces from each column name
                cleaned_row = [column.strip() if isinstance(column, str) else column for column in row]
                table_data.append(cleaned_row)
        
        
        
        Telephone_Pattern = r"Telephone:\s+?(\d.*)"
        Email_Pattern = r"Email:\s+?(\w.+)"
        Company_Number_Pattern = r"Company\s+Number:\s+?(\d.+)"
        VAT_Pattern = r"VAT\s+Number:\s+(\d.*)"
        Business_Name_Pattern = r"Business\s+Name:\s+?(\w.*)"
        Account_Terms_Pattern = r"Account\s+Terms:\s+?(\w.*)"
        Invoice_Date_Pattern = r"Invoice\s+Date:\s+?(\w.*)"
        Invoice_Number_Pattern = r"Invoice\s+Number:\s+?(\w.*)"

        NET_TOTAL_Pattern = r"NET\s+TOTAL:\s+?(\w.*)"

        elephone = []
        Email = []
        Company_Number = []
        VAT_Number = []
        Business_Name = []
        Account_Terms = []
        Invoice_Date = []
        Invoice_Number = []
        Total_payable = []
        NET_TOTAL = []

        text = page.extract_text()
        Telephone = re.search(Telephone_Pattern, text, re.IGNORECASE)
        Email = re.search(Email_Pattern, text, re.IGNORECASE)
        Company_Number = re.search(Company_Number_Pattern, text)
        VAT_Number =   re.search(VAT_Pattern, text)
        Business_Name = re.search(Business_Name_Pattern, text, re.IGNORECASE)
        Account_Terms = re.search(Account_Terms_Pattern, text, re.IGNORECASE)
        Invoice_Date = re.search(Invoice_Date_Pattern, text)
        Invoice_Number = re.search(Invoice_Number_Pattern, text, re.IGNORECASE)

        # if Telephone:
        #     print(f"Telephone: {Telephone.group(1)}")
        # if Email:
        #     print(f"Email: {Email.group(1)}")
        # if Company_Number:
        #     print(f"Company_Number: {Company_Number.group(1)}")
        # if VAT_Number:
        #     print(f"VAT_Number: {VAT_Number.group(1)}")
        # if Business_Name:
        #     print(f"Business_Name: {Business_Name.group(1)}")
        # if Account_Terms:
        #     print(f"Account_Terms: {Account_Terms.group(1)}")
        # if Invoice_Date:
        #     print(f"Invoice_Date: {Invoice_Date.group(1)}")
        # if Invoice_Number:
        #     print(f"Invoice_Number: {Invoice_Number.group(1)}")
        
        
        NET_pattern = r"NET\s+TOTAL:(.*)"
        vat_pattern = r"VAT\s+@\s+20%:(.*)"
        invoice_total_pattern = r"INVOICE\s+TOTAL:(.*)"
        total_payable_pattern = r"Total\s(\w.*)"
        payment_due_pattern = r"Payment\s(\w.*)"

        match1 = re.search(NET_pattern, pdf_text)
        match2 = re.search(vat_pattern, pdf_text)
        match3 = re.search(invoice_total_pattern, pdf_text)
        match4 = re.search(total_payable_pattern, pdf_text)
        match5 = re.search(payment_due_pattern, pdf_text)

        if match1:
            NET_value = match1.group(1)
            # print(f"NET TOTAL: {NET_value}")
        if match2:
            vat_value = match2.group(1)
            # print(f"VAT: {vat_value}")
        if match3:
            invoice_total_value = match3.group(1)
            # print(f"INVOICE TOTAL: {invoice_total_value}")
        if match4:
            total_payable = match4.group(1)
            # print(f"TOTAL PAYABLE: {total_payable}")
        if match5:
            payment_due = match5.group(1)
            # print(f"Payment due: {payment_due}")
            
        # These coordinates should define a rectangular region that includes the entire table.
        areas = [
        [60, 200, 120, 400],
        [60, 400, 120, 600],
        [440, 80, 550, 650],
        ]
        tables = tabula.read_pdf(pdf_file_path, pages='1', area=areas)

        table1 = tabula.read_pdf(pdf_file_path, pages=1, area=[45, 200, 120, 440])[0]
        #table2 = tabula.read_pdf(pdf_file_path, pages=1, area=[47, 400, 120, 600])[0]
        table2 = tabula.read_pdf(pdf_file_path, pages=1, area=[44, 480, 120, 600])[0]
        #print(table1)
        #print(table2)

        #Vehicle Details Table
        table3 = tabula.read_pdf(pdf_file_path, pages=1, area=[420, 70, 550, 140])[0]
        table11 = tabula.read_pdf(pdf_file_path, pages=1, area=[430, 140, 550, 200])[0] #CUSTOMER_NAME Column
        table4 = tabula.read_pdf(pdf_file_path, pages=1, area=[410, 190, 540, 290])[0]
        table5 = tabula.read_pdf(pdf_file_path, pages=1, area=[400, 290, 470, 340])[0]

        table6 = tabula.read_pdf(pdf_file_path, pages=1, area=[410, 290, 550, 340])[0]
        table7 = tabula.read_pdf(pdf_file_path, pages=1, area=[420, 332, 530, 375])[0]
        table8 = tabula.read_pdf(pdf_file_path, pages=1, area=[420, 390, 550, 440],guess=True)[0]
        table9 = tabula.read_pdf(pdf_file_path, pages=1, area=[435, 450, 550, 530])[0] #done
        table10 = tabula.read_pdf(pdf_file_path, pages=1, area=[430, 520, 510, 580])[0] #done

        values_in_column1 = []
        values_in_column2 = []

        values_in_column3 = []
        values_in_column4 = []
        values_in_column5 = []
        values_in_column6 = []
        values_in_column7 = []
        values_in_column8 = []
        values_in_column9 = []
        values_in_column10 = []
        values_in_column11 = []
        
        
        for _, row in table1.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column1 = row.iloc[0]
            values_in_column1.append(value_in_column1)

        for _, row in table2.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column2 = row.iloc[0]
            values_in_column2.append(value_in_column2)

        for _, row in table3.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column3 = row.iloc[0]
        #value_in_column3 = row.iloc[1]
            values_in_column3.append(value_in_column3)

        for _, row in table4.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column4 = row.iloc[0]
        #value_in_column3 = row.iloc[1]
            values_in_column4.append(value_in_column4)

        for _, row in table5.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column5 = row.iloc[0]
        #value_in_column3 = row.iloc[1]
            values_in_column5.append(value_in_column5)

        for _, row in table6.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column6 = row.iloc[0]
        #value_in_column3 = row.iloc[1]
            values_in_column6.append(value_in_column6)

        for _, row in table7.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column7 = row.iloc[0]
        #value_in_column3 = row.iloc[1]
            values_in_column7.append(value_in_column7)

        for _, row in table8.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column8 = row.iloc[0]
        #value_in_column3 = row.iloc[1]
            values_in_column8.append(value_in_column8)

        print(values_in_column8)

        for _, row in table9.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column9 = row.iloc[0]
        #value_in_column3 = row.iloc[1]
            values_in_column9.append(value_in_column9)

        for _, row in table10.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column10 = row.iloc[0]
        #value_in_column3 = row.iloc[1]
            values_in_column10.append(value_in_column10)

        for _, row in table11.iterrows():
        #Access data by column index (0, 1, 2, ...)
            value_in_column11 = row.iloc[0]
        #value_in_column11 = row.iloc[1]
            values_in_column11.append(value_in_column11)

        # combined_values1 = ', '.join(values_in_column1)  # Join the values with a delimiter
        # combined_values1 = combined_values1.replace(', ', '<br>')
        
        # combined_values2 = ', '.join(values_in_column2)
        # combined_values2 = combined_values2.replace(', ', '<br>')
        # combined_values8 = ",  ".join(values_in_column8)
        # combined_values8 = combined_values8.replace(', ', '<br>')
        # combined_values9 = ",  ".join(values_in_column9)
        # combined_values9 = combined_values9.replace(', ', '<br>')

        #print(combined_values8)
        #print(values_in_column10)
        combined_values10 = [f'{value:.2f}' for value in values_in_column10] # adding two leading zeroes because python during conversion removes it
        # combined_values10 = ",  ".join(combined_values10)
        #combined_values9 = ', '.join(str(val) for val in values_in_column9) #CONVERSION DUE TO INT VALUE, JOIN DOES NOT WORK FOR INT
        # combined_values10 = combined_values10.replace(', ', '<br>')
        
        combined_values1 = json.dumps(values_in_column1)
        combined_values2 = json.dumps(values_in_column2)
        combined_values8 = json.dumps(values_in_column8)
        combined_values9 = json.dumps(values_in_column9)
        combined_values10 = json.dumps(combined_values10)
        
        NET_value = float(NET_value[2:])
        vat_value = float(vat_value[2:])
        invoice_total_value = float(invoice_total_value[2:])
        
        logging.info(f"{file}")
        
        
        ks61_instance = KS61(
        Registered_Business_Address=combined_values1,
        Telephone=Telephone.group(1),
        Email=Email.group(1),
        Company_Number=Company_Number.group(1),
        Vat_Number=VAT_Number.group(1),
        Trading_Address=combined_values2,
        Business_Name=Business_Name.group(1),
        Account_Terms=Account_Terms.group(1),
        Invoice_Date=Invoice_Date.group(1),
        Invoice_Number=Invoice_Number.group(1),
        Date=value_in_column3,
        Customer_Name=value_in_column11,
        Authorisation_Number=value_in_column4,
        Make=value_in_column6,
        Model=value_in_column7,
        Registration=combined_values8,
        Description_of_Work=combined_values9,
        Price=combined_values10,
        Net_Total=NET_value,
        Vat_at_20_Percent=vat_value,
        Invoice_Total=invoice_total_value,
        Total_Payable='Total ' + total_payable,
        Payment_Due='Payment ' + payment_due,
        file = invoice
        )
        
        invoice.status = "Processed"
        invoice.message = ""
        invoice = invoice.save()
        
        
        
        logging.info("Created invoice_instance")
        
        ks61_instance.save()
        
        logging.info(f"{ks61_instance}")
        
        message = f"File {file} added."
            
        logging.info(message)
    
                
        return {
            'success': True,
            'message': 'Data extraction successful',
            'pdf_text': pdf_text,  # You can include additional extracted data if needed
        }
    except Exception as e:
        logging.info(f"Error {e}")
        return {
            'success': False,
            'message': f'Error during data extraction: {str(e)}'
        }