from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Sum
from .models import Food, Weight
from .forms import FoodForm, WeightForm

# Create your views here.

class FoodListView(LoginRequiredMixin, ListView):
    model = Food
    template_name = 'nutrition/food_list.html'
    context_object_name = 'foods'

    def get_queryset(self):
        return Food.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['weight_form'] = WeightForm()
        context['latest_weight'] = Weight.objects.filter(
            user=self.request.user
        ).first()
        return context

class FoodDetailView(LoginRequiredMixin, DetailView):
    model = Food
    template_name = 'nutrition/food_detail.html'

    def get_queryset(self):
        return Food.objects.filter(user=self.request.user)

class FoodCreateView(LoginRequiredMixin, CreateView):
    model = Food
    form_class = FoodForm
    template_name = 'nutrition/food_form.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class FoodUpdateView(LoginRequiredMixin, UpdateView):
    model = Food
    form_class = FoodForm
    template_name = 'nutrition/food_form.html'

    def get_queryset(self):
        return Food.objects.filter(user=self.request.user)

class FoodDeleteView(LoginRequiredMixin, DeleteView):
    model = Food
    template_name = 'nutrition/food_confirm_delete.html'
    success_url = reverse_lazy('nutrition:food_list')

    def get_queryset(self):
        return Food.objects.filter(user=self.request.user)
