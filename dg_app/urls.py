from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from . import utils

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('login', views.login_view, name='login'),
    path('register', views.register_user, name='register'),
    path('logout', LogoutView.as_view(next_page="login"), name='logout'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('pdf_view/', views.pdf_view, name="pdf_view"),
    path('pdf_view/<int:invoice_id>/', views.pdf_view, name="pdf_view_with_id"),
    path('file_upload', views.file_upload, name='file_upload'),
    path('invoice_data', views.invoice_data, name='invoice_data'),
    path('user_profile', views.user_profile, name='user_profile'),
    path('rej_to_proc/<int:id>/', views.direct_data_extractor, name='direct_data_extractor'),
    path('rej_to_disc/<int:id>/', views.discard_invoice, name='discard_invoice'),
    path('upload_csv', utils.upload_csv, name="upload_csv"),
    path('export_csv', utils.export_csv, name="export_csv"),
]
