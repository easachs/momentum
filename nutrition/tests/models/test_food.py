from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from nutrition.models import Food

class FoodModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.food = Food.objects.create(
            user=self.user,
            date=timezone.localtime(timezone.now()).date(),
            name="Test Food",
            calories=500,
            protein=20,
            carbs=50,
        )

    def test_food_creation(self):
        self.assertEqual(self.food.name, "Test Food")
        self.assertEqual(self.food.calories, 500)
        self.assertEqual(self.food.protein, 20)
        self.assertEqual(self.food.carbs, 50)

    def test_food_str_representation(self):
        expected = f"Test Food ({self.food.date})"
        self.assertEqual(str(self.food), expected)
