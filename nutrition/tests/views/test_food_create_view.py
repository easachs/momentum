from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from nutrition.models import Food

class FoodCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")
        self.today = timezone.localtime(timezone.now()).date()

    def test_food_create_view(self):
        food_data = {
            "date": self.today,
            "name": "Test Food",
            "calories": 500,
            "protein": 20,
            "carbs": 50,
        }
        response = self.client.post(reverse("nutrition:food_create"), food_data)
        self.assertEqual(Food.objects.count(), 1)
        food = Food.objects.first()
        self.assertEqual(food.name, "Test Food")
