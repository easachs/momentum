from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from books.models import Book

class BookListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        # Create some test books
        self.book1 = Book.objects.create(
            user=self.user,
            title="Book A",
            author="Author A",
            status="TBR"
        )
        self.book2 = Book.objects.create(
            user=self.user,
            title="Book B",
            author="Author B",
            status="RDG"
        )

    def test_book_list_view(self):
        response = self.client.get(reverse("books:book_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "books/book_list.html")
        self.assertEqual(len(response.context["books"]), 2)

    def test_status_filtering(self):
        response = self.client.get(reverse("books:book_list") + "?status=TBR")
        self.assertEqual(len(response.context["books"]), 1)
        self.assertEqual(response.context["books"][0], self.book1)

    def test_sorting(self):
        response = self.client.get(reverse("books:book_list") + "?sort=author")
        books = list(response.context["books"])
        self.assertEqual(books[0], self.book1)  # Author A comes before Author B

    def test_unauthorized_access(self):
        self.client.logout()
        response = self.client.get(reverse("books:book_list"))
        self.assertEqual(response.status_code, 302)  # Redirects to login
