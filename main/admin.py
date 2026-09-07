from django.contrib import admin
from .models import UserProfile, Match, Bet, ScoreBet, WinnerBet, Thread, Message

# Register your models here.

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'points_balance', 'favourite_team')

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('team1', 'team2', 'result', 'fixture_id', 'match_status')

@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'bet_amount_display', 'match_display', 'bet_time', 'bet_type', 'bet_return', 'bet_status')

    def user_display(self, obj):
        return obj.user.username if obj.user else None

    user_display.short_description = 'User'

    def bet_amount_display(self, obj):
        return obj.bet_amount

    bet_amount_display.short_description = 'Bet Amount'

    def match_display(self, obj):
        return f"{obj.match.team1} vs {obj.match.team2}" if obj.match else None

    match_display.short_description = 'Match'

@admin.register(ScoreBet)
class ScoreBetAdmin(admin.ModelAdmin):
    list_display = ('bet_display', 'bet_amount_display','bet_status_display', 'match_display','bet_return_display', 'home_team_score', 'away_team_score')

    def bet_display(self, obj):
        return obj.bet.user.username if obj.bet.user else None
    
    def bet_return_display(self, obj):
        return obj.bet.bet_return if obj.bet.user else None
    
    def bet_status_display(self, obj):
        return obj.bet.bet_status if obj.bet.user else None

    bet_display.short_description = 'User'

    def bet_amount_display(self, obj):
        return obj.bet.bet_amount

    bet_amount_display.short_description = 'Bet Amount'

    def match_display(self, obj):
        return f"{obj.bet.match.team1} vs {obj.bet.match.team2}" if obj.bet.match else None

    match_display.short_description = 'Match'

@admin.register(WinnerBet)
class WinnerBetAdmin(admin.ModelAdmin):
    list_display = ('bet_display', 'bet_amount_display', 'match_display', 'winning_team')

    def bet_display(self, obj):
        return obj.bet.user.username if obj.bet.user else None

    bet_display.short_description = 'User'

    def bet_amount_display(self, obj):
        return obj.bet.bet_amount

    bet_amount_display.short_description = 'Bet Amount'

    def match_display(self, obj):
        return f"{obj.bet.match.team1} vs {obj.bet.match.team2}" if obj.bet.match else None

    match_display.short_description = 'Match'

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('thread', 'sender', 'content')


