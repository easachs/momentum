# Project: Momentum

## Purpose
Momentum is a habit and job application tracker built using Django. It helps users manage their habits, track streaks, and collaborate with friends. It also includes a feature for tracking job applications, allowing users to manage job-related contacts, statuses, and links.

## Structure

### `tracker` app: Manages all habit-related functionality, including:
- Habit creation and management (CRUD operations).
- Dashboard visualization of habit progress.
- Habit streak tracking.

###	`jobhunt` app: Focused on managing job applications and professional networking:
- CRUD operations for job applications and contacts.
- Analytics dashboard to track application statuses (e.g., total applications, interviews scheduled).
- Badges for milestones like submitting 5/10/20 applications, receiving 1/5/10 interviews, adding a contact.
- Optional tracking of contacts for networking purposes.

###	`theme` app: Handles front-end styling and design integration:
- Implements Tailwind CSS for consistent and responsive UI.

###	`social` app: Manages user interactions and collaboration:
- Features for adding friends and viewing their dashboards.
- Leaderboard for friendly competition among users.
- Milestone achievements with badges (make a friend, 10/50/100 habit completions, 7/30 day streaks for a habit in each category).
- Social sharing of progress (e.g., completed habits, streaks, badges).

## Features
- Google OAuth-based authentication (no traditional username/password).

- Habit tracking with:
  - Daily and weekly habit streaks tracked per habit (current and longest streak).
  - Habits categorized by category and completion rate for each category shown on main dashboard.
  - Badges for milestones (7/30 day streaks for a habit in each category, 10/50/100 total completions).
  - Reminders about daily habits not yet completed today, and weekly habits not yet completed this week.
  - Leaderboard of users, sorted by habit completion rate.

- Job application tracking:
  - Metrics for total applications, applications by status, and offer rate shown on main dashboard.
  - Upcoming applications (with close due dates) have notifications on application list.
  - Application list prioritizes showing recently edited applications first.

- Social Features:
  - Add friends to see their own dashboards (without ability to edit).
  - Leaderboard rankings based on completion rate (or total badges earned).

## Stack
- Django
- Tailwind CSS
- SQLite (plan to switch to Postgres)
- Pytest

## Coding Preferences:
- Follow Django best practices.
- Use class-based views (CBVs) for CRUD operations.
- Write tests for models, views, and integration.
- Use Tailwind for consistent and reusable UI components.
- Modularize templates with partials for shared elements.

## Roadmap
- MVP Goals:
  - Full CRUD for habits and job applications (done).
  - Dashboard with analytics for both habits and job applications.
  - Basic Google OAuth-based authentication (done).
  - Styling with Tailwind CSS for all pages.

- Stretch Goals:
  - Gamification of progress (e.g., habit streak battles between friends).
  - Advanced analytics for job applications.
  - Mobile-first design for accessibility.
