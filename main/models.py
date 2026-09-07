from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')  
    points_balance = models.IntegerField(default=500)
    favourite_team = models.CharField(max_length=100, blank=True, null=True)
    total_points_placed=models.IntegerField(default=0)
    total_points_won=models.IntegerField(default=0)
    percentage_of_points_won = models.FloatField(default=0.0)
    last_login_date = models.DateField(null=True, blank=True)

    def update_last_login_date(self):
        self.last_login_date = timezone.now().date()
        self.save()

class Match(models.Model):
    team1 = models.CharField(max_length=100)
    team2 = models.CharField(max_length=100)
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)
    result = models.CharField(max_length=100)
    fixture_id=models.IntegerField(null=True, blank=True)
    match_status = models.CharField(max_length=10, default=None)

class Bet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, default=None)
    bet_amount = models.IntegerField()
    bet_time = models.DateTimeField()
    bet_type = models.CharField(max_length=20, choices=[('Winner', 'Winner Bet'), ('Score', 'Score Bet')], null=True)
    bet_return = models.IntegerField(null=True, blank=True)
    bet_status= models.CharField(max_length=10,choices= [('pending', 'Pending'),('won', 'Won'),('lost', 'Lost')],default='pending')

class ScoreBet(models.Model):
    bet = models.OneToOneField(Bet, on_delete=models.CASCADE, related_name='score_bet')
    home_team_score = models.IntegerField()
    away_team_score = models.IntegerField()
    score_prediction = models.CharField(max_length=10, blank=True, null=True)


class WinnerBet(models.Model):
    bet = models.OneToOneField(Bet, on_delete=models.CASCADE, related_name='winner_bet')
    winning_team = models.CharField(max_length=100)

class Thread(models.Model):
    title = models.CharField(max_length=200)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)

class Message(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    

