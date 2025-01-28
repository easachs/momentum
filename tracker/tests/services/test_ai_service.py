from datetime import timedelta
from unittest import mock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from tracker.models import Habit, HabitCompletion, AIHabitSummary
from tracker.services.ai.ai_service import AIHabitService
from jobhunt.models import Application

class TestAIHabitService(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.service = AIHabitService()

        # Create some test habits
        self.habit1 = Habit.objects.create(
            user=self.user,
            name="Exercise",
            frequency="daily",
            category="health"
        )
        self.habit2 = Habit.objects.create(
            user=self.user,
            name="Reading",
            frequency="weekly",
            category="learning"
        )

        # Add some completions
        today = timezone.localtime(timezone.now()).date()
        HabitCompletion.objects.create(
            habit=self.habit1,
            completed_at=today
        )
        HabitCompletion.objects.create(
            habit=self.habit2,
            completed_at=today - timedelta(days=2)
        )

        # Create test applications
        self.today = timezone.now()
        self.month_ago = self.today - timedelta(days=30)
        
        # Store the application instances
        self.recent_app1 = Application.objects.create(
            user=self.user,
            company="Recent Active Co",
            title="Recent Position",
            status="interviewing",
            created_at=self.today - timedelta(days=5)
        )
        self.recent_app2 = Application.objects.create(
            user=self.user,
            company="Recent Co",
            title="Recent Position",
            status="applied",
            created_at=self.today - timedelta(days=15)
        )
        self.old_app = Application.objects.create(
            user=self.user,
            company="Old Co",
            title="Old Position",
            status="rejected",
            created_at=self.today - timedelta(days=45)
        )

    @mock.patch('tracker.services.ai.ai_service.OpenAI')
    def test_generate_habit_summary_success(self, mock_openai):
        # Mock OpenAI response
        mock_client = mock.MagicMock()
        mock_openai.return_value = mock_client
        mock_response = mock.MagicMock()
        mock_response.choices = [
            mock.MagicMock(
                message=mock.MagicMock(
                    content="Test summary content"
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        # Set the mocked client on the service instance
        self.service.client = mock_client

        # Generate summary
        summary_content = self.service.generate_habit_summary(self.user)

        self.assertEqual(summary_content, "Test summary content")
        mock_client.chat.completions.create.assert_called_once()

    def test_generate_habit_summary_no_habits(self):
        # Delete all habits
        Habit.objects.all().delete()

        summary_content = self.service.generate_habit_summary(self.user)
        self.assertEqual(summary_content, "No habits found to analyze.")

    @mock.patch('tracker.services.ai.ai_service.OpenAI')
    def test_create_summary_success(self, mock_openai):
        # Mock OpenAI response
        mock_client = mock.MagicMock()
        mock_openai.return_value = mock_client
        mock_response = mock.MagicMock()
        mock_response.choices = [
            mock.MagicMock(
                message=mock.MagicMock(
                    content="Test summary content"
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        # Set the mocked client on the service instance
        self.service.client = mock_client

        # Create summary
        summary, error = self.service.create_summary(self.user)

        self.assertIsNone(error)
        self.assertIsInstance(summary, AIHabitSummary)
        self.assertEqual(summary.content, "Test summary content")
        self.assertEqual(summary.user, self.user)

    @mock.patch('tracker.services.ai.ai_service.OpenAI')
    def test_create_summary_api_error(self, mock_openai):
        # Mock OpenAI error
        mock_client = mock.MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        # Set the mocked client on the service instance
        self.service.client = mock_client

        # Try to create summary
        summary, error = self.service.create_summary(self.user)

        self.assertIsNone(summary)
        self.assertEqual(error, "Error: API Error")
        self.assertEqual(AIHabitSummary.objects.count(), 0)

    def test_gather_habit_stats(self):
        stats = self.service._gather_habit_stats(self.user.habits.all())

        self.assertEqual(len(stats), 2)
        self.assertEqual(stats[0]['name'], "Exercise")
        self.assertEqual(stats[0]['frequency'], "daily")
        self.assertEqual(stats[1]['name'], "Reading")
        self.assertEqual(stats[1]['frequency'], "weekly")

    def test_build_prompt(self):
        habit_context = [
            {
                'name': 'Exercise',
                'frequency': 'daily',
                'streak': 1,
                'monthly_completions': 1,
                'category': 'health'
            }
        ]

        application_context = {
            'total': 2,
            'recent': 1,
            'active': 1
        }

        prompt = self.service._build_prompt('testuser', habit_context, application_context)

        # Test existing habit assertions
        self.assertIn('testuser', prompt)
        self.assertIn('Exercise', prompt)
        self.assertIn('health', prompt)
        self.assertIn('streak: 1', prompt.lower())

        # Test new application assertions
        self.assertIn('Job Search Status', prompt)
        self.assertIn('Total Applications: 2', prompt)
        self.assertIn('Applications in Last 30 Days: 1', prompt)
        self.assertIn('Active Applications: 1', prompt)

    def test_build_prompt_no_applications(self):
        """Test prompt building when user has no applications"""
        habit_context = [
            {
                'name': 'Exercise',
                'frequency': 'daily',
                'streak': 1,
                'monthly_completions': 1,
                'category': 'health'
            }
        ]

        application_context = {
            'total': 0,
            'recent': 0,
            'active': 0
        }

        prompt = self.service._build_prompt('testuser', habit_context, application_context)

        # Should not include job search section when no applications
        self.assertNotIn('Job Search Status', prompt)
        self.assertIn('Exercise', prompt)  # Still includes habit info

    @mock.patch('tracker.services.ai.ai_service.OpenAI')
    def test_generate_habit_summary_with_applications(self, mock_openai):
        # Mock OpenAI response
        mock_client = mock.MagicMock()
        mock_response = mock.MagicMock()
        mock_response.choices = [mock.MagicMock(message=mock.MagicMock(content="Test summary"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        self.service.client = mock_client

        # Delete using the stored instance
        self.old_app.delete()

        summary = self.service.generate_habit_summary(self.user)
        prompt = mock_client.chat.completions.create.call_args_list[0].kwargs['messages'][1]['content']
        
        self.assertIn("Exercise", prompt)
        self.assertIn("Job Search Status", prompt)
        self.assertIn("Total Applications: 2", prompt)
        self.assertIn("Applications in Last 30 Days: 2", prompt)
        self.assertIn("Active Applications: 2", prompt)

    def test_gather_application_stats(self):
        # Delete using the stored instance
        self.old_app.delete()

        stats = self.service._gather_application_stats(self.user)
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['recent'], 2)
        self.assertEqual(stats['active'], 2) 