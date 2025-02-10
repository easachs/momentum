from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from nutrition.models import Weight

class WeightModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.weight = Weight.objects.create(
            user=self.user, date=timezone.localtime(timezone.now()).date(), weight=180
        )

    def test_weight_creation(self):
        self.assertEqual(self.weight.weight, 180)

    def test_weight_str_representation(self):
        expected = f"180lbs on {self.weight.date}"
        self.assertEqual(str(self.weight), expected)
