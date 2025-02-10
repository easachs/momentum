from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from nutrition.models import Food

class FoodUpdateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")
        self.today = timezone.localtime(timezone.now()).date()

    def test_food_update_view(self):
        food = Food.objects.create(
            user=self.user,
            date=self.today,
            name="Test Food",
            calories=500,
            protein=20,
            carbs=50,
        )
        update_data = {
            "date": self.today,
            "name": "Updated Food",
            "calories": 600,
            "protein": 25,
            "carbs": 55,
        }
        response = self.client.post(
            reverse("nutrition:food_update", kwargs={"pk": food.pk}), update_data
        )
        food.refresh_from_db()
        self.assertEqual(food.name, "Updated Food")
        self.assertEqual(food.calories, 600)
