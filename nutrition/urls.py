from django.urls import path
from . import views

app_name = 'nutrition'

urlpatterns = [
    path('', views.FoodListView.as_view(), name='food_list'),
    path('food/create/', views.FoodCreateView.as_view(), name='food_create'),
    path('food/<int:pk>/', views.FoodDetailView.as_view(), name='food_detail'),
    path('food/<int:pk>/edit/', views.FoodUpdateView.as_view(), name='food_update'),
    path('food/<int:pk>/delete/', views.FoodDeleteView.as_view(), name='food_delete'),
]
