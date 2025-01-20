from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Application

class ApplicationListView(LoginRequiredMixin, ListView):
    model = Application
    template_name = 'jobhunt/application_list.html'
    context_object_name = 'applications'

    def get_queryset(self):
        queryset = Application.objects.filter(user=self.request.user)
        status = self.request.GET.get('status')
        if status and status != 'all':
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Application.STATUS_CHOICES
        return context

class ApplicationDetailView(DetailView):
    model = Application
    template_name = 'jobhunt/application_detail.html'

class ApplicationCreateView(LoginRequiredMixin, CreateView):
    model = Application
    template_name = 'jobhunt/application_form.html'
    fields = ['company', 'job_title', 'status', 'job_link', 'notes']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('jobhunt:application_list')

class ApplicationUpdateView(LoginRequiredMixin, UpdateView):
    model = Application
    template_name = 'jobhunt/application_form.html'
    fields = ['company', 'job_title', 'status', 'job_link', 'notes']

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse('jobhunt:application_list')

class ApplicationDeleteView(LoginRequiredMixin, DeleteView):
    model = Application
    template_name = 'jobhunt/application_confirm_delete.html'
    success_url = reverse_lazy('jobhunt:application_list')

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user)
