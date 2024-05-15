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
from django.db.models import Count, Sum, Q
from decimal import Decimal
from django.views.decorators.csrf import csrf_protect
from django.core.files.storage import default_storage

# def generate_invoice_total_pie_chart_for_dashboard(target_date):
#     # Group by 'Make' and calculate the sum of 'Invoice_Total'
#     result = (
#         KS61.objects
#         .filter(Invoice_Date=target_date)
#         .values('Make')
#         .annotate(total_invoices_total=Sum('Invoice_Total'))
#     )

#     # Convert the result to a Pandas DataFrame
#     df = pd.DataFrame(result)

#     # Round the 'total_invoices_total' field to 2 decimal points
#     df['total_invoices_total'] = df['total_invoices_total'].apply(lambda x: Decimal(x).quantize(Decimal('0.00')))

#     # Create a pie chart using Plotly
#     data = [go.Pie(labels=df['Make'], values=df['total_invoices_total'])]
#     layout = go.Layout(title=f'Invoice Total Distribution for {target_date}')
#     fig = go.Figure(data=data, layout=layout)

#     # Convert the Plotly figure to HTML
#     chart_html = pyo.plot(fig, output_type='div', include_plotlyjs=False)
    
#     return chart_html

# def plot_top_invoices_and_count_for_dashboard(target_date):
#     # Get top 5 invoices for the specified date
#     top_invoices = (
#         KS61.objects
#         .filter(Invoice_Date=target_date)
#         .values('Make', 'Invoice_Total', 'Customer_Name')
#         .order_by('-Invoice_Total')[:5]
#     )

#     # Create a DataFrame from the result
#     df = pd.DataFrame(top_invoices)

#     # Sort the DataFrame by 'Invoice_Total' in descending order
#     df = df.sort_values(by='Invoice_Total', ascending=False)

#     # Add a unique identifier to each row
#     df['id'] = range(1, len(df) + 1)

#     # Plot using Plotly Express with a default color for all bars
#     fig = go.Figure()

#     fig.add_trace(go.Bar(
#         x=df['Make'],
#         y=df['Invoice_Total'],
#         marker_color='blue',  # Use a default color (e.g., 'blue')
#         text=df['id'],
#         textposition='outside',
#         customdata=df['Customer_Name'],
#         hovertemplate='%{x}<br>Total Invoice: %{y}<br>Customer: %{customdata}',
#     ))

#     fig.update_layout(
#         title=f'Top 5 Invoices for {target_date}',
#         xaxis_title='Make',
#         yaxis_title='Total Invoice',
#         barmode='stack',
#     )

#     # Save the plot as HTML
#     chart_html = pyo.plot(fig, output_type='div')

#     return chart_html


def generate_invoice_total_pie_chart_for_dashboard(values):
    # Group by 'Make' and calculate the sum of 'Invoice_Total'
    result = (
        values
        .values('Make').exclude(Make__isnull = True)
        .annotate(total_invoices_total=Sum('Invoice_Total'))
    )
    
    if not result:
        return None
    
    # Convert the result to a Pandas DataFrame
    df = pd.DataFrame(result)
    
    # Round the 'total_invoices_total' field to 2 decimal points
    df['total_invoices_total'] = df['total_invoices_total'].apply(lambda x: Decimal(x).quantize(Decimal('0.00')))

    # Create a pie chart using Plotly
    data = [go.Pie(labels=df['Make'], values=df['total_invoices_total'])]
    layout = go.Layout(title='Invoices Value Distribution')
    fig = go.Figure(data=data, layout=layout)

    # Convert the Plotly figure to HTML
    chart_html = pyo.plot(fig, output_type='div', include_plotlyjs=False)

    return chart_html

def plot_top_invoices_and_count_for_dashboard(values):
    # Get top 5 invoices from the entire database
    top_invoices = (
        values
        .values('Make', 'Invoice_Total', 'Customer_Name')
        .exclude(Q(Make__isnull=True)|Q(Invoice_Total__isnull=True)|Q(Customer_Name__isnull=True))
        .order_by('-Invoice_Total')[:5]
    )
    
    if not top_invoices:
        return None

    # Create a DataFrame from the result
    df = pd.DataFrame(top_invoices)

    # Sort the DataFrame by 'Invoice_Total' in descending order
    df = df.sort_values(by='Invoice_Total', ascending=False)

    # Add a unique identifier to each row
    df['id'] = range(1, len(df) + 1)

    # Define custom colors for each bar
    custom_colors = ['blue', 'green', 'red', 'purple', 'orange']

    # Plot using Plotly Express with custom colors for all bars
    fig = go.Figure()

    for i in range(len(df)):
        fig.add_trace(go.Bar(
            x=[df['Make'].iloc[i]],
            y=[df['Invoice_Total'].iloc[i]],
            marker_color=custom_colors[i],
            text=[df['id'].iloc[i]],
            textposition='outside',
            customdata=[df['Customer_Name'].iloc[i]],
            hovertemplate='%{x}<br>Total Invoice: %{y}<br>Customer: %{customdata}',
        ))

    fig.update_layout(
        title='Top 5 Invoices',
        xaxis_title='Make',
        yaxis_title='Total Invoice',
    )

    # Save the plot as HTML
    chart_html = pyo.plot(fig, output_type='div')

    return chart_html

def generate_invoice_total_over_time_chart(values):
    # Group by 'created_at' and calculate the sum of 'Invoice_Total'
    result = (
        values
        .values('created_at')
        .exclude(created_at__isnull=True)
        .annotate(total_invoice_value=Sum('Invoice_Total'))
        .order_by('created_at')
    )
    
    if not result:
        return None

    # Convert the result to a Pandas DataFrame
    df = pd.DataFrame(result)

    # Create a line chart using Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['created_at'], y=df['total_invoice_value'], mode='lines+markers', name='Total Invoice Value'))

    fig.update_layout(
        title='Periodical Invoice value',
        xaxis_title='Date',
        yaxis_title='Total Invoice Value',
    )

    # Convert the Plotly figure to HTML
    chart_html = pyo.plot(fig, output_type='div', include_plotlyjs=False)

    return chart_html

def generate_invoice_distribution_by_business_name(values):
    # Group by 'Business_Name' and calculate the count of invoices
    result = (
        values
        .values('Business_Name')
        .exclude(Business_Name__is_null = True)
        .annotate(invoice_count=Count('id'))
    )
    
    if not result:
        return None

    # Convert the result to a Pandas DataFrame
    df = pd.DataFrame(result)

    # Create a bar chart using Plotly
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Business_Name'], y=df['invoice_count'], name='Invoice Count', marker_color='blue'))

    fig.update_layout(
        title='Distribution of Invoices by Business Name',
        xaxis_title='Business Name',
        yaxis_title='Invoice Count',
    )

    # Convert the Plotly figure to HTML
    chart_html = pyo.plot(fig, output_type='div', include_plotlyjs=False)

    return chart_html

def generate_top_invoices_chart(values):
    # Get top 5 invoices by 'Invoice_Total'
    top_invoices = (
        values
        .values('Invoice_Number', 'Invoice_Total', 'Customer_Name', 'Business_Name')
        .exclude(Q(Invoice_Number__isnull = True) | Q(Invoice_Total__isnull = True) | Q(Customer_Name__isnull = True) | Q(Business_Name__isnull = True))
        .order_by('-Invoice_Total')
    )
    
    if not top_invoices:
        return None

    # Convert the result to a Pandas DataFrame
    df = pd.DataFrame(top_invoices)

    # Create a bar chart using Plotly
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['Invoice_Number'],
        y=df['Invoice_Total'],
        name='Top Invoices',
        marker_color='green',
        hovertemplate='Invoice Number: %{x}<br>Total Invoice: %{y}<br>Customer: %{customdata[0]}<br>Business: %{customdata[1]}',
        customdata=df[['Customer_Name', 'Business_Name']]
    ))

    fig.update_layout(
        title='Top Invoices',
        xaxis_title='Invoice Number',
        yaxis_title='Invoice Total',
    )

    # Convert the Plotly figure to HTML
    chart_html = pyo.plot(fig, output_type='div', include_plotlyjs=False)

    return chart_html

def generate_invoice_value_vs_net_total_scatter(values):
    # Get 'Invoice_Total' and 'Net_Total' for each record
    result = (
        values
        .values('Invoice_Total', 'Net_Total', 'Invoice_Number', 'Customer_Name', 'Business_Name')
        .exclude(Q(Invoice_Total__isnull = True)  | Q(Net_Total__isnull = True) | Q(Customer_Name__isnull = True) | Q(Business_Name__isnull = True))
    )
    
    if not result:
        return None
    
    # Convert the result to a Pandas DataFrame
    df = pd.DataFrame(result)

    # Create a scatter plot using Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Invoice_Total'],
        y=df['Net_Total'],
        mode='markers',
        name='Invoice vs. Net Total',
        marker_color='orange',
        hovertemplate='Invoice Total: %{x}<br>Net Total: %{y}<br>Invoice Number: %{customdata[0]}<br>Customer: %{customdata[1]}<br>Business: %{customdata[2]}',
        customdata=df[['Invoice_Number', 'Customer_Name', 'Business_Name']]
    ))

    fig.update_layout(
        title='Total Invoice Value vs. Net Total',
        xaxis_title='Invoice Total',
        yaxis_title='Net Total',
    )

    # Convert the Plotly figure to HTML
    chart_html = pyo.plot(fig, output_type='div', include_plotlyjs=False)

    return chart_html

def generate_invoices_per_make_donut_chart(values):
    # Get the number of invoices per make
    result = (
        values
        .values('Make')
        .exclude(Make__isnull=True)
        .annotate(total_invoices=Count('id'))
    )
    
    if not result:
        return None

    # Convert the result to a Pandas DataFrame
    df = pd.DataFrame(result)

    # Create a donut chart using Plotly
    fig = go.Figure(go.Pie(
        labels=df['Make'],
        values=df['total_invoices'],
        hole=0.3,
        textinfo='label+percent',
        hoverinfo='label+value+percent',
        marker=dict(colors=px.colors.qualitative.Plotly),
    ))

    fig.update_layout(
        title='Invoices per vendor',
        title_x=0.5,  # Center the title
        annotations=[dict(text='', x=0.5, y=0.5, font_size=20, showarrow=False)],
    )

    # Convert the Plotly figure to HTML
    chart_html = pyo.plot(fig, output_type='div', include_plotlyjs=False)

    return chart_html