from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Application, Contact
from .forms import ApplicationForm, ContactForm
from django.db import models
from django.utils import timezone

class ApplicationListView(LoginRequiredMixin, ListView):
    model = Application
    template_name = 'jobhunt/application_list.html'
    context_object_name = 'applications'

    def get_queryset(self):
        queryset = Application.objects.filter(user=self.request.user)
        status = self.request.GET.get('status')
        if status and status != 'all':
            queryset = queryset.filter(status=status)
        
        # Always sort by due date, with nulls last
        queryset = queryset.order_by(
            models.F('due').asc(nulls_last=True),
            '-created_at'
        )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Application.STATUS_CHOICES
        context['contact_form'] = ContactForm()
        context['contacts'] = Contact.objects.filter(user=self.request.user)
        return context

class ApplicationDetailView(DetailView):
    model = Application
    template_name = 'jobhunt/application_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        return context

class ApplicationCreateView(LoginRequiredMixin, CreateView):
    model = Application
    template_name = 'jobhunt/application_form.html'
    form_class = ApplicationForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('jobhunt:application_detail', kwargs={'pk': self.object.pk})

class ApplicationUpdateView(LoginRequiredMixin, UpdateView):
    model = Application
    template_name = 'jobhunt/application_form.html'
    form_class = ApplicationForm

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse('jobhunt:application_detail', kwargs={'pk': self.object.pk})

class ApplicationDeleteView(LoginRequiredMixin, DeleteView):
    model = Application
    template_name = 'jobhunt/application_confirm_delete.html'
    success_url = reverse_lazy('jobhunt:application_list')

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user)

class ContactCreateView(LoginRequiredMixin, CreateView):
    model = Contact
    form_class = ContactForm
    template_name = 'jobhunt/contact_form.html'
    success_url = reverse_lazy('jobhunt:application_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ContactUpdateView(LoginRequiredMixin, UpdateView):
    model = Contact
    form_class = ContactForm
    template_name = 'jobhunt/contact_form.html'
    success_url = reverse_lazy('jobhunt:application_list')

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)

class ContactDeleteView(LoginRequiredMixin, DeleteView):
    model = Contact
    template_name = 'jobhunt/contact_confirm_delete.html'
    success_url = reverse_lazy('jobhunt:application_list')

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)

class ContactDetailView(LoginRequiredMixin, DetailView):
    model = Contact
    template_name = 'jobhunt/contact_detail.html'

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        return context
