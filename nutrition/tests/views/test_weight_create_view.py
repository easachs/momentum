from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from nutrition.models import Weight

class WeightCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")
        self.today = timezone.localtime(timezone.now()).date()

    def test_weight_create_view(self):
        """Test creating a new weight entry"""
        weight_data = {
            "date": self.today,
            "weight": 180
        }
        response = self.client.post(reverse("nutrition:weight_create"), weight_data)
        
        # Should redirect back to food list
        self.assertRedirects(response, reverse("nutrition:food_list"))
        
        # Verify weight was created
        self.assertEqual(Weight.objects.count(), 1)
        weight = Weight.objects.first()
        self.assertEqual(weight.weight, 180)
        self.assertEqual(weight.user, self.user)

    def test_weight_update_existing(self):
        """Test that adding a weight for an existing date updates it"""
        # Create initial weight
        initial_weight = Weight.objects.create(
            user=self.user,
            date=self.today,
            weight=180
        )
        
        # Try to create another weight for same date
        weight_data = {
            "date": self.today,
            "weight": 185
        }
        response = self.client.post(reverse("nutrition:weight_create"), weight_data)
        
        # Should redirect back to food list
        self.assertRedirects(response, reverse("nutrition:food_list"))
        
        # Should still be only one weight
        self.assertEqual(Weight.objects.count(), 1)
        
        # Verify weight was updated
        updated_weight = Weight.objects.get(id=initial_weight.id)
        self.assertEqual(updated_weight.weight, 185)

    def test_unauthorized_weight_create(self):
        """Test that logged out users can't create weights"""
        self.client.logout()
        weight_data = {
            "date": self.today,
            "weight": 180
        }
        response = self.client.post(reverse("nutrition:weight_create"), weight_data)
        self.assertEqual(response.status_code, 302)  # Redirects to login
        self.assertEqual(Weight.objects.count(), 0)
