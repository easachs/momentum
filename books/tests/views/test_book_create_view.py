from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from books.models import Book
from django.utils import timezone

class BookCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_book_create_view(self):
        book_data = {
            "title": "New Book",
            "author": "New Author",
            "pages": 300,
            "genre": "FIC",
            "status": "TBR"
        }
        response = self.client.post(reverse("books:book_create"), book_data)
        self.assertEqual(Book.objects.count(), 1)
        book = Book.objects.first()
        self.assertEqual(book.title, "New Book")
        self.assertEqual(book.user, self.user)

    def test_book_create_minimal_fields(self):
        """Test creating a book with only required fields"""
        book_data = {
            "title": "Minimal Book",
            "status": "TBR",
            "genre": "FIC"  # Add default genre since it's required
        }
        response = self.client.post(reverse("books:book_create"), book_data)
        self.assertRedirects(response, reverse("books:book_list"))
        self.assertEqual(Book.objects.count(), 1)
        book = Book.objects.first()
        self.assertEqual(book.title, "Minimal Book")
        self.assertEqual(book.author, "")
        self.assertIsNone(book.pages)

    def test_unauthorized_create(self):
        self.client.logout()
        book_data = {
            "title": "Test Book",
            "status": "TBR"
        }
        response = self.client.post(reverse("books:book_create"), book_data)
        self.assertEqual(response.status_code, 302)  # Redirects to login
        self.assertEqual(Book.objects.count(), 0)

    def test_invalid_book_create(self):
        """Test that invalid data doesn't create a book"""
        book_data = {
            "title": "",  # Title is required
            "status": "TBR",
            "genre": "FIC"
        }
        response = self.client.post(reverse("books:book_create"), book_data)
        self.assertEqual(response.status_code, 200)  # Returns to form
        self.assertEqual(Book.objects.count(), 0)
        self.assertContains(response, "This field is required")  # Changed assertion

    def test_create_with_dates(self):
        """Test creating a book with start and finish dates"""
        today = timezone.now().date()
        book_data = {
            "title": "Date Test Book",
            "status": "CMP",
            "genre": "FIC",  # Add required genre
            "date_started": today - timezone.timedelta(days=10),
            "date_finished": today
        }
        response = self.client.post(reverse("books:book_create"), book_data)
        self.assertRedirects(response, reverse("books:book_list"))
        self.assertEqual(Book.objects.count(), 1)
        book = Book.objects.first()
        self.assertEqual(book.status, "CMP")
        self.assertEqual(book.date_finished, today)
