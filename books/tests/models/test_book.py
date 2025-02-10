from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from books.models import Book
from django.core.exceptions import ValidationError

class BookModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.book = Book.objects.create(
            user=self.user,
            title="Test Book",
            author="Test Author",
            pages=200,
            genre="FIC",
            status="TBR"
        )

    def test_book_creation(self):
        self.assertEqual(self.book.title, "Test Book")
        self.assertEqual(self.book.author, "Test Author")
        self.assertEqual(self.book.pages, 200)
        self.assertEqual(self.book.genre, "FIC")
        self.assertEqual(self.book.status, "TBR")
        self.assertIsNone(self.book.rating)
        self.assertIsNone(self.book.date_started)
        self.assertIsNone(self.book.date_finished)

    def test_book_str_representation(self):
        expected = "Test Book (To Be Read)"
        self.assertEqual(str(self.book), expected)

    def test_optional_fields(self):
        book = Book.objects.create(
            user=self.user,
            title="Minimal Book",
            status="TBR"
        )
        self.assertEqual(book.title, "Minimal Book")
        self.assertEqual(book.author, "")
        self.assertIsNone(book.pages)
        self.assertEqual(book.genre, "FIC")  # Default value

    def test_rating_validation(self):
        # Valid rating
        self.book.rating = 5
        self.book.save()
        self.assertEqual(self.book.rating, 5)

        # Invalid rating
        with self.assertRaises(ValidationError):
            self.book.rating = 6
            self.book.full_clean()  # This triggers validation
            self.book.save()

    def test_invalid_status(self):
        """Test that invalid status raises validation error"""
        with self.assertRaises(ValidationError):
            self.book.status = "INVALID"
            self.book.full_clean()

    def test_invalid_genre(self):
        """Test that invalid genre raises validation error"""
        with self.assertRaises(ValidationError):
            self.book.genre = "INVALID"
            self.book.full_clean()

    def test_date_validation(self):
        """Test that finished date can't be before start date"""
        self.book.date_started = timezone.now().date()
        self.book.date_finished = self.book.date_started - timezone.timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.book.full_clean()
