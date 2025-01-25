import os
import openai
import logging
from openai import OpenAI
from django.utils import timezone
from datetime import timedelta
from tracker.models import AIHabitSummary

logger = logging.getLogger(__name__)

class AIHabitService:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        self.client = OpenAI(api_key=api_key)
    
    def generate_habit_summary(self, user):
        """Generate an AI summary of user's habits and progress"""
        try:
            habits = user.habits.all()
            if not habits.exists():
                return "No habits found to analyze."

            habit_context = self._gather_habit_stats(habits)
            prompt = self._build_prompt(user.username, habit_context)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an encouraging AI assistant that helps users track their habits. "
                            "Provide insights, encouragement, and suggestions in a friendly tone. "
                            "Format your response in markdown."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return response.choices[0].message.content
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return f"Error: {str(e)}"
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Error: {str(e)}"
    
    def _gather_habit_stats(self, habits):
        today = timezone.now().date()
        month_ago = today - timedelta(days=30)
        
        return [{
            'name': habit.name,
            'frequency': habit.frequency,
            'streak': habit.current_streak(),
            'monthly_completions': habit.completions.filter(
                completed_at__gte=month_ago
            ).count(),
            'category': habit.category
        } for habit in habits]
    
    def _build_prompt(self, username, habit_context):
        prompt = f"Analyze the following habits and progress for {username}:\n\n"
        
        for habit in habit_context:
            prompt += f"- {habit['name']} ({habit['category']})\n"
            prompt += f"  * Frequency: {habit['frequency']}\n"
            prompt += f"  * Current streak: {habit['streak']}\n"
            prompt += f"  * Completions in last 30 days: {habit['monthly_completions']}\n\n"
        
        prompt += "\nPlease provide:\n"
        prompt += "A brief summary of overall progress\n"
        prompt += "Achievements to celebrate\n"
        prompt += "Suggestions for improvement\n"
        prompt += "A motivational quote related to their habits\n"
        prompt += "Avoid clarifying questions or using emojis.\n"
        
        return prompt

    def create_summary(self, user):
        """Create and save a new AI summary"""
        try:
            # Generate the summary content
            summary_content = self.generate_habit_summary(user)
            
            if summary_content.startswith('Error:'):
                return None, summary_content
            
            # Create the summary object
            summary = AIHabitSummary.objects.create(
                user=user,
                content=summary_content
            )
            
            return summary, None  # Return summary and no error
            
        except Exception as e:
            logger.error(f"Error in create_summary: {str(e)}")
            return None, 'An unexpected error occurred'