from django.test import TestCase
from django.contrib.auth.models import User
from main.models import UserProfile, Bet, Match, WinnerBet, ScoreBet
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

class Select_favourite_Team_View(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_redirect_after_selecting_favourite_team(self):
        # Log in the user
        self.client.login(username='testuser', password='testpassword')

        # Send a POST request with form data to the select_favourite_team page
        response = self.client.post(reverse('select_favourite_team'), {'selected_team': 'Test_Team'})

        # Check if the response status code is 302 (redirect)
        self.assertEqual(response.status_code, 302)

        # Check if the response redirects to the home page
        self.assertRedirects(response, reverse('home'))

class HomeView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        user_profile = UserProfile.objects.get(user=self.user)
        user_profile.favourite_team = 'Test_Team'
        user_profile.save()

    
    def test_home_view_news(self):
        # Log in the user
        self.client.login(username='testuser', password='testpassword')
        
        # Mock the get_team_news function
        with patch('main.views.get_team_news') as mock_get_team_news:
            mock_get_team_news.return_value = [{'title': 'Test News', 'description': 'Test Description', 'url': 'http://testurl.com', 'image_url': 'http://testimageurl.com'}]
            
            # Get the home page
            response = self.client.get(reverse('home'))
            
            # Check if the news data is passed to the template context
            self.assertTrue('news_data' in response.context)
            news_data = response.context['news_data']
            self.assertEqual(len(news_data), 1)
            self.assertEqual(news_data[0]['title'], 'Test News')
            self.assertEqual(news_data[0]['description'], 'Test Description')
            self.assertEqual(news_data[0]['url'], 'http://testurl.com')
            self.assertEqual(news_data[0]['image_url'], 'http://testimageurl.com')
            
            # Check if the get_team_news function is called with the correct arguments
            mock_get_team_news.assert_called_once_with('Test_Team')

class PLTableViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

        # Set the user's favourite team
        user_profile = UserProfile.objects.get(user=self.user)
        user_profile.favourite_team = 'Test Team'
        user_profile.save()

    @patch('main.views.requests.get')
    def test_PLtable_view_api_call(self, mock_get):
        # Set up mocked response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": [
                {
                    "league": {
                        "standings": [
                            {
                                "table": [
                                    {"position": 1, "team": "Team A"},
                                    {"position": 2, "team": "Team B"},
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        # Log in the user
        self.client.login(username='testuser', password='testpassword')

        # Get the PL table page
        response = self.client.get(reverse('PLtable'))

        # Check if the API call was made with the correct URL, headers, and parameters
        mock_get.assert_called_once_with(
            "https://api-football-v1.p.rapidapi.com/v3/standings",
            headers={
                "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
                "x-rapidapi-key": FOOTBALL_API_KEY,
            },
            params={"league": "39", "season": "2023"},
        )



class NotificationsTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='test_user', password='test_password')
        # Create a test match
        self.match = Match.objects.create(team1='Team A', team2='Team B', fixture_id=1, match_status='FT', home_score=2, away_score=1)

    def test_winner_bet_notification(self):
        self.client.login(username='test_user', password='test_password')
        
        # Create a test winner bet
        bet = Bet.objects.create(user=self.user, match=self.match, bet_amount=50, bet_return=60, bet_time=timezone.now(), bet_type='Winner') 

        # Ensure bet is successful
        winner_bet = WinnerBet.objects.create(bet=bet, winning_team='Team A')  

        # Ensure that the user receives a success notification
        response = self.client.get(reverse('home'), follow=True)  
        self.assertContains(response, 'Congratulations! You won the Winner bet')
        
        # Create a new test winner bet
        new_bet = Bet.objects.create(user=self.user, match=self.match, bet_amount=50, bet_return=60, bet_time=timezone.now(), bet_type='Winner') 

        # Ensure bet has failed
        new_winner_bet = WinnerBet.objects.create(bet=new_bet, winning_team='Team B')  

        # Ensure that the user receives a failure notification
        response = self.client.get(reverse('home'), follow=True)  
        self.assertContains(response, 'Unfortunately, you lost the Winner bet')

    def test_score_bet_notification(self):
        self.client.login(username='test_user', password='test_password')
        # Create a test score bet
        bet = Bet.objects.create(user=self.user, match=self.match, bet_amount=50, bet_return = 60, bet_time=timezone.now(), bet_type='Score')
        bet.save()
        # Ensure bet is successful
        ScoreBet.objects.create(bet=bet, home_team_score=2, away_team_score=1, score_prediction='2:1') 

        # Ensure that the user receives a success notification
        response = self.client.get(reverse('home'), follow=True)  
        self.assertContains(response, 'Congratulations! You won the Score bet')

        new_bet = Bet.objects.create(user=self.user, match=self.match, bet_amount=50, bet_return=60, bet_time=timezone.now(), bet_type='Score') 

        # Ensure bet has failed
        new_score_bet = ScoreBet.objects.create(bet=new_bet, home_team_score=1, away_team_score=0, score_prediction='1:0')  

        # Ensure that the user receives a failure notification
        response = self.client.get(reverse('home'), follow=True)  
        self.assertContains(response, 'Unfortunately, you lost the Score bet')

    def test_weekly_points_notification(self):
        self.client.login(username='test_user', password='test_password')
        # Simulate a weekly login by updating the last login date
        self.user.user_profile.last_login_date = timezone.now() - timezone.timedelta(days=8)  # Assuming last login was 8 days ago
        self.user.user_profile.save()
        # Ensure that the user receives a success notification for weekly points
        response = self.client.get(reverse('home'), follow=True)  
        self.assertContains(response, 'Congratulations! You have won')



class HomeViewTestCase(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        # Create a user profile for the user
        self.user_profile = UserProfile.objects.create(user=self.user)

    @patch('main.views.spin_wheel', return_value=500)  # Mock the spin_wheel function to return a fixed value for testing
    def test_points_on_first_login_of_week(self, mock_spin_wheel):
        # Set the last login date of the user to a date that is not in the current week
        last_week_date = datetime.now().date() - timedelta(days=7)
        self.user_profile.last_login_date = last_week_date
        self.user_profile.save()

        # Log the user in by making a GET request to the home view
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get('/')

        # Check that the user's points balance has increased by the mock value returned by spin_wheel
        self.user_profile.refresh_from_db()  # Refresh the user profile from the database to get the updated points balance
        self.assertEqual(self.user_profile.points_balance, 1000) 