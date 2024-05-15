from django.shortcuts import render, redirect
import psycopg2
import subprocess
import pandas as pd
from .models import KS61, Invoices
from .forms import InvoicesForm
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import plotly.express as px
import plotly.graph_objects as go
import plotly.offline as pyo
import seaborn as sns
import matplotlib.pyplot as plt
from django.db.models import Count, Sum
from decimal import Decimal
from django.views.decorators.csrf import csrf_protect
from django.core.files.storage import default_storage
def get_and_show_invoice_count_for_date(target_date):
    # Assuming Date field in KS61 model is of type CharField storing date as string
    # If Date is actually a DateField in the model, you can skip the conversion
    invoice_count = (
        KS61.objects
        .filter(Date=target_date)
        .aggregate(invoice_count=Count('Date'))
    )['invoice_count']
    
    print(invoice_count)
    # Create a simple text visualization using Plotly
    fig = go.Figure()

    fig.add_trace(
        go.Indicator(
            mode="number",
            value=invoice_count,
            title="Invoice Count",
            number={'font': {'size': 40}},
        )
    )

    fig.update_layout(title_text=f'Invoice Count for {target_date}')
    fig.show()
    
#print(get_and_show_invoice_count_for_date('18/09/2023'))

def generate_and_show_bar_chart(target_date):
    result = (
        KS61.objects
        .filter(Date=target_date)
        .values('Make')
        .annotate(total_invoices_total=Sum('Invoice_Total'))
    )

    # Round the 'total_invoices_total' field to 2 decimal points
    for entry in result:
        entry['total_invoices_total'] = Decimal(entry['total_invoices_total']).quantize(Decimal('0.00'))

    # Convert the result to a Pandas DataFrame
    df = pd.DataFrame(result)

    # Create a bar chart using Plotly Express
    fig = px.bar(df, x='Make', y='total_invoices_total', title=f'Total Invoices Total by Maker on {target_date}')
    fig.update_layout(xaxis_title='Make', yaxis_title='Total Invoices Total')

    # Show the plot
    fig.show()

#print(generate_and_show_bar_chart('18/09/2023'))


def plot_top_invoices_and_count(target_date):
     # Get top 5 invoices for the specified date
    top_invoices = (
        KS61.objects
        .filter(Invoice_Date=target_date)
        .values('Make', 'Invoice_Total', 'Customer_Name')
        .order_by('-Invoice_Total')[:5]
    )

    # Create a DataFrame from the result
    df = pd.DataFrame(top_invoices)

    # Sort the DataFrame by 'Invoice_Total' in descending order
    df = df.sort_values(by='Invoice_Total', ascending=False)

    # Add a unique identifier to each row
    df['id'] = range(1, len(df) + 1)

    # Plot using Plotly Express with 'Customer_Name', 'Price', 'Make' as text on each bar
    fig = px.bar(df, x='Make', y='Invoice_Total', color='Customer_Name',
             labels={'Invoice_Total': 'Total Invoice'},
             title=f'Top 5 Invoices for {target_date}',
             text='id')
    # Show the plot
    fig.show()

#print(plot_top_invoices_and_count('11/10/2023'))

# def plot_top_invoices_and_count_seaborn(target_date):
#     # Get top 5 invoices for the specified date
#     top_invoices = (
#         KS61.objects
#         .filter(Invoice_Date=target_date)
#         .values('Make', 'Invoice_Total', 'Customer_Name')
#         .order_by('-Invoice_Total')[:5]
#     )

#     # Create a DataFrame from the result
#     df = pd.DataFrame(top_invoices)

#     # Plot using Seaborn in non-interactive mode
#     with sns.plotting_context("notebook", font_scale=1.2):
#         plt.figure(figsize=(12, 6))
#         sns.barplot(data=df, x='Make', y='Invoice_Total', hue='Customer_Name')
#         plt.title(f'Top 5 Invoices for {target_date}')
#         plt.xlabel('Make')
#         plt.ylabel('Total Invoice')
#         plt.tight_layout()

#     # Save the plot to a file or return the plot as needed
#     plt.savefig('top_invoices_plot.png')

# # Call the function
# plot_top_invoices_and_count_seaborn('11/10/2023')

def plot_top_invoices_and_count(target_date):
    # Get top 5 invoices for the specified date
    top_invoices = (
        KS61.objects
        .filter(Invoice_Date=target_date)
        .values('Make', 'Invoice_Total', 'Customer_Name')
        .order_by('-Invoice_Total')[:5]
    )

    # Create a DataFrame from the result
    df = pd.DataFrame(top_invoices)

    # Sort the DataFrame by 'Invoice_Total' in descending order
    df = df.sort_values(by='Invoice_Total', ascending=False)

    # Add a unique identifier to each row
    df['id'] = range(1, len(df) + 1)

    # Plot using Plotly Express with 'Customer_Name', 'Price', 'Make' as text on each bar
    fig = px.bar(df, x='Make', y='Invoice_Total', color='Customer_Name',
                 labels={'Invoice_Total': 'Total Invoice'},
                 title=f'Top 5 Invoices for {target_date}',
                 text='id')

    # Show the plot
    fig.show()

    # # Group by 'Make' and calculate the sum of 'Invoice_Total' for each 'Make'
    # grouped_df = df.groupby('Make')['Invoice_Total'].sum().reset_index()

    # # Plot a pie chart for the sum of 'Invoice_Total' for each 'Make'
    # pie_fig = px.pie(grouped_df, names='Make', values='Invoice_Total',
    #                  title=f'Sum of Invoices Total by Make for {target_date}')

    # Show the pie chart
    # pie_fig.show()

#print(plot_top_invoices_and_count('11/10/2023'))

def generate_invoice_total_pie_chart(target_date):
    # Group by 'Make' and calculate the sum of 'Invoice_Total'
    result = (
        KS61.objects
        .filter(Invoice_Date=target_date)
        .values('Make')
        .annotate(total_invoices_total=Sum('Invoice_Total'))
    )

    # Convert the result to a Pandas DataFrame
    df = pd.DataFrame(result)

    # # Round the 'total_invoices_total' field to 2 decimal points
    df['total_invoices_total'] = df['total_invoices_total'].apply(lambda x: Decimal(x).quantize(Decimal('0.00')))

    # # Create a pie chart using Plotly
    fig = px.pie(df, names='Make', values='total_invoices_total', title=f'Invoice Total Distribution for {target_date}')
    fig.show()

#print(generate_invoice_total_pie_chart('11/10/2023'))
