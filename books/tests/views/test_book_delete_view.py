from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from books.models import Book

class BookDeleteViewTest(TestCase):
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

    def test_book_delete_view(self):
        response = self.client.post(
            reverse("books:book_delete", kwargs={"pk": self.book.pk})
        )
        self.assertEqual(Book.objects.count(), 0)
        self.assertRedirects(response, reverse("books:book_list"))

    def test_unauthorized_delete(self):
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
        
        # Try to delete other user's book
        response = self.client.post(
            reverse("books:book_delete", kwargs={"pk": other_book.pk})
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Book.objects.count(), 2)  # Both books still exist

    def test_get_delete_confirmation(self):
        """Test that GET request shows delete confirmation page"""
        response = self.client.get(
            reverse("books:book_delete", kwargs={"pk": self.book.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "books/book_confirm_delete.html")
