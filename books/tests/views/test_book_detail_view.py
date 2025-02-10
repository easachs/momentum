from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from books.models import Book

class BookDetailViewTest(TestCase):
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
            status="TBR"
        )

    def test_book_detail_view(self):
        response = self.client.get(
            reverse("books:book_detail", kwargs={"pk": self.book.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "books/book_detail.html")
        self.assertEqual(response.context["book"], self.book)

    def test_unauthorized_access(self):
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
        
        # Try to access other user's book
        response = self.client.get(
            reverse("books:book_detail", kwargs={"pk": other_book.pk})
        )
        self.assertEqual(response.status_code, 404)
