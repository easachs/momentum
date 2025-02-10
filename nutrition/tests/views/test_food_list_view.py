from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

class FoodListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")
        self.today = timezone.localtime(timezone.now()).date()

    def test_food_list_view(self):
        response = self.client.get(reverse("nutrition:food_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "nutrition/food_list.html")
