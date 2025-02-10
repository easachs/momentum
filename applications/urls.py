from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    path('', views.ApplicationListView.as_view(), name='application_list'),
    path('create/', views.ApplicationCreateView.as_view(), name='application_create'),
    path('<int:pk>/', views.ApplicationDetailView.as_view(), name='application_detail'),
    path('<int:pk>/edit/', views.ApplicationUpdateView.as_view(), name='application_update'),
    path('<int:pk>/delete/', views.ApplicationDeleteView.as_view(), name='application_delete'),
    path('contacts/create/', views.ContactCreateView.as_view(), name='contact_create'),
    path('contacts/<int:pk>/edit/', views.ContactUpdateView.as_view(), name='contact_edit'),
    path('contacts/<int:pk>/delete/', views.ContactDeleteView.as_view(), name='contact_delete'),
    path('contacts/<int:pk>/', views.ContactDetailView.as_view(), name='contact_detail'),
]
