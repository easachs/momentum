from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from books.models import Book

class BookUpdateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")
        self.book = Book.objects.create(
            user=self.user,
            title="Test Book",
            author="Test Author",
            pages=200,
            genre="FIC",
            status="TBR"
        )

    def test_book_update_view(self):
        update_data = {
            "title": "Updated Book",
            "author": "Updated Author",
            "pages": 250,
            "genre": "NON",
            "status": "RDG"
        }
        response = self.client.post(
            reverse("books:book_update", kwargs={"pk": self.book.pk}),
            update_data
        )
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, "Updated Book")
        self.assertEqual(self.book.author, "Updated Author")
        self.assertEqual(self.book.status, "RDG")

    def test_unauthorized_update(self):
        # Create another user and their book
        other_user = get_user_model().objects.create_user(
            username="otheruser",
            password="testpass123"
        )
        other_book = Book.objects.create(
            user=other_user,
            title="Other Book",
            status="TBR"
        )
        
        # Try to update other user's book
        update_data = {
            "title": "Hacked Book",
            "status": "TBR"
        }
        response = self.client.post(
            reverse("books:book_update", kwargs={"pk": other_book.pk}),
            update_data
        )
        self.assertEqual(response.status_code, 404)
        other_book.refresh_from_db()
        self.assertEqual(other_book.title, "Other Book")  # Title unchanged
