from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Sum
from django.contrib import messages
from django.utils import timezone
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
        today = timezone.localtime(timezone.now()).date()

        # Get today's foods
        todays_foods = Food.objects.filter(
            user=self.request.user,
            date=today
        )

        # Calculate daily totals
        context['daily_totals'] = {
            'calories': todays_foods.aggregate(Sum('calories'))['calories__sum'] or 0,
            'protein': todays_foods.aggregate(Sum('protein'))['protein__sum'] or 0,
            'carbs': todays_foods.aggregate(Sum('carbs'))['carbs__sum'] or 0,
        }

        context['weight_form'] = WeightForm(initial={'date': today})
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

class WeightCreateView(LoginRequiredMixin, View):
    def post(self, request):
        date = request.POST.get('date')
        weight = request.POST.get('weight')

        try:
            # Try to get existing weight entry for this date
            existing_weight = Weight.objects.get(
                user=request.user,
                date=date
            )
            # Update existing weight
            existing_weight.weight = weight
            existing_weight.save(update_fields=['weight', 'updated_at'])
            messages.success(request, "Weight updated successfully.")
        except Weight.DoesNotExist:
            # Create new weight entry
            Weight.objects.create(
                user=request.user,
                date=date,
                weight=weight
            )
            messages.success(request, "Weight logged successfully.")

        return redirect('nutrition:food_list')
