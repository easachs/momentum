from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Book
from .forms import BookForm

class BookListView(LoginRequiredMixin, ListView):
    model = Book
    template_name = 'books/book_list.html'
    context_object_name = 'books'

    def get_queryset(self):
        queryset = Book.objects.filter(user=self.request.user)

        # Handle status filtering
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Handle sorting
        sort = self.request.GET.get('sort')
        if sort:
            if sort == 'date_started':
                queryset = queryset.order_by('-date_started', 'title')
            elif sort == 'date_finished':
                queryset = queryset.order_by('-date_finished', 'title')
            elif sort == 'author':
                queryset = queryset.order_by('author', 'title')
            elif sort == 'pages':
                queryset = queryset.order_by('-pages', 'title')
            elif sort == 'status':
                queryset = queryset.order_by('status', 'title')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Book.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['current_sort'] = self.request.GET.get('sort', '')
        return context

class BookDetailView(LoginRequiredMixin, DetailView):
    model = Book
    template_name = 'books/book_detail.html'

    def get_queryset(self):
        return Book.objects.filter(user=self.request.user)

class BookCreateView(LoginRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_form.html'
    success_url = reverse_lazy('books:book_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('books:book_list')

class BookUpdateView(LoginRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_form.html'

    def get_queryset(self):
        return Book.objects.filter(user=self.request.user)

class BookDeleteView(LoginRequiredMixin, DeleteView):
    model = Book
    template_name = 'books/book_confirm_delete.html'
    success_url = reverse_lazy('books:book_list')

    def get_queryset(self):
        return Book.objects.filter(user=self.request.user)
