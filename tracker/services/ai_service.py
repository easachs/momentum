import os
import openai
import logging
from openai import OpenAI
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

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
            
            logger.info(f"Sending request to OpenAI for user {user.username}")
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
        prompt += "1. A brief summary of overall progress\n"
        prompt += "2. Specific achievements to celebrate\n"
        prompt += "3. Encouraging suggestions for improvement\n"
        prompt += "4. A motivational quote or funny quip related to their habits\n"
        
        return prompt 