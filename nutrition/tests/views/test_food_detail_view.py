from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from nutrition.models import Food

class FoodDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")
        self.today = timezone.localtime(timezone.now()).date()

    def test_food_detail_view(self):
        food = Food.objects.create(
            user=self.user,
            date=self.today,
            name="Test Food",
            calories=500,
            protein=20,
            carbs=50,
        )
        response = self.client.get(
            reverse("nutrition:food_detail", kwargs={"pk": food.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "nutrition/food_detail.html")
        self.assertEqual(response.context["food"], food)

    def test_unauthorized_access(self):
        # Create another user
        other_user = get_user_model().objects.create_user(
            username="otheruser", password="testpass123"
        )
        # Create food entry for other user
        food = Food.objects.create(
            user=other_user,
            date=self.today,
            name="Other Food",
            calories=500,
            protein=20,
            carbs=50,
        )
        # Try to access other user's food
        response = self.client.get(
            reverse("nutrition:food_detail", kwargs={"pk": food.pk})
        )
        self.assertEqual(response.status_code, 404)
