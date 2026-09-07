from django.shortcuts import render, redirect
import requests, pickle
from datetime import datetime
from operator import itemgetter
from django.contrib.auth.decorators import login_required
from .models import User, UserProfile, Match, Bet, ScoreBet, WinnerBet, Thread, Message
from django.utils import timezone
from django.contrib import messages
from fractions import Fraction
from django.db.models import Count, Sum
from django.core.cache import cache
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

                                                         
@login_required(login_url='/')
def home(request):
    """
    Renders the home page.
    Updates user's points if a new week has started since their last login.
    Redirects to select_favourite_team if favourite team is not set.
    Retrieves favourite team's news.
    """
    getfixtures(request) # Updates any matches
    # Bets are then handled
    handle_winner_bets(request, request.user)
    handle_score_prediction_bets(request, request.user)
    user_profile = UserProfile.objects.get(user=request.user)
    
    if user_profile.last_login_date is not None:
        last_login_week = user_profile.last_login_date.isocalendar()[1]
        current_week = datetime.now().date().isocalendar()[1]

        if last_login_week != current_week:
            points_earned = spin_wheel()
            user_profile.points_balance += points_earned  
            user_profile.save()
            messages.success(request, f'Congratulations! You have won {points_earned} points for logging in this week.')

    user_profile.update_last_login_date()
    
    if not user_profile.favourite_team:
       
        return redirect('select_favourite_team')

    favourite_team = user_profile.favourite_team
    news_data = get_team_news(favourite_team)
   
    messages_exist = bool(messages.get_messages(request))

    return render(request, 'main/home.html', {'user_profile': user_profile,'messages_exist': messages_exist,'news_data': news_data})

def spin_wheel():
    """
    Simulates spinning a wheel to win points.
    """
    prizes = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    
    lambda_parameter = 0.004
    
    probabilities = lambda_parameter * np.exp(-lambda_parameter * np.array(prizes))
    probabilities /= np.sum(probabilities)  
    
    prize = np.random.choice(prizes, p=probabilities)

    return prize 

def leaderboard(request):
    """
    Renders the leaderboard page.
    Retrieves user data and sorts based on percentage of points won.
    """
    users_data = []
    
    for user in User.objects.all():
        user_profile = UserProfile.objects.get(user=user)
        users_data.append({
            'username': user.username,
            'points':user_profile.points_balance,
            'total_points_placed': user_profile.total_points_placed,
            'total_points_won': user_profile.total_points_won,
            'percentage_of_points_won': user_profile.percentage_of_points_won,
            'favourite_team': user_profile.favourite_team
        })

    users_data = sorted(users_data, key=lambda x: (x['percentage_of_points_won'], x['total_points_placed']), reverse=True)

    user_profile = UserProfile.objects.get(user=request.user)
    context = {'users_data': users_data, 'user_profile': user_profile}
    return render(request, 'main/leaderboard.html', context)

def get_premier_league_teams():
    """
    Retrieves Premier League teams' data from an external API.
    Saves the data to a file for future use.
    """
    try:
        with open("premier_league_teams_data.pkl", "rb") as file:
            return pickle.load(file)
    except (FileNotFoundError, EOFError):
        pass
    current_season = get_current_season()
    url = "https://api-football-v1.p.rapidapi.com/v3/teams"
    querystring = {"league": "39", "season": current_season}
    headers = {
        "X-RapidAPI-Key": FOOTBALL_API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    data = response.json().get('response', [])

    logos = []
    for team in data:
        team_id = team.get("team", {}).get("id")
        logo_url = f"https://api-football-v1.p.rapidapi.com/v3/teams?id={team_id}"
        logo_response = requests.get(logo_url, headers=headers)
        logo_data = logo_response.json().get('response', [{}])[0].get("team", {}).get("logo")
        logos.append(logo_data)

    premier_league_teams_with_logos = [{"name": team.get("team", {}).get("name"), "logo": logo} for team, logo in zip(data, logos)]
    premier_league_teams_with_logos = sorted(premier_league_teams_with_logos, key=lambda x: x["name"])

    with open("premier_league_teams_data.pkl", "wb") as file:
        pickle.dump(premier_league_teams_with_logos, file)

    return premier_league_teams_with_logos



@login_required(login_url='/')
def bet_history(request):
    """
    Renders the bet history page.
    Groups user's bets by date and retrieves relevant data for display.
    """
    user_profile = UserProfile.objects.get(user=request.user)
    user_bets_grouped = ( 
        Bet.objects
        .filter(user=request.user)
        .values('bet_time__date')
        .annotate(bet_count=Count('id'), bets=Count('id'))
        .order_by('-bet_time__date')
    )

    
    for group in user_bets_grouped:
        group['bets'] = Bet.objects.filter(
            user=request.user,
            bet_time__date=group['bet_time__date']
        ).order_by('-bet_time')

        for bet in group['bets']:
            if bet.bet_type == 'Winner':
                bet.winner_prediction = WinnerBet.objects.get(bet=bet).winning_team
            elif bet.bet_type == 'Score':
                score_bet = ScoreBet.objects.get(bet=bet)
                bet.home_score_prediction = score_bet.home_team_score
                bet.away_score_prediction = score_bet.away_team_score
    
    return render(request, 'main/bet_history.html', {'user_bets_grouped': user_bets_grouped, 'user_profile': user_profile})

@login_required(login_url='/')
def select_favourite_team(request):
    """
    Renders the page for selecting favourite team.
    Retrieves Premier League teams' data.
    Saves selected team to user profile.
    """
    user_profile = UserProfile.objects.get(user=request.user) 
    if request.method == 'POST':
        selected_team = request.POST.get('selected_team')
        if selected_team:
            user_profile.favourite_team = selected_team
            user_profile.save()
            return redirect('home')
        else:
            messages.error(request, 'Please select a favourite team.')
            return render(request, 'main/select_favourite_team.html', {'premier_league_teams': get_premier_league_teams(), 'user_profile': user_profile})
    else:
        return render(request, 'main/select_favourite_team.html', {'premier_league_teams': get_premier_league_teams(), 'user_profile': user_profile})




def get_team_news(favourite_team):
    """
    Retrieves news related to the favourite team from an external API.
    Caches the news data for future use.
    """
    search_query = f'{favourite_team}'

    cached_news = cache.get(f'news_{search_query}')

    if cached_news:
        return cached_news
    
    else:
        url = "https://gnews.io/api/v4/search"
        params = {
            "q": search_query,
            "lang": "en",
            "token": GNEWS_API_KEY
        }

        response = requests.get(url, params=params)
        data = response.json()
        articles = data.get('articles', [])

        news_list = []
        unique_image_urls = set()

        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')
            url = article.get('url', '')
            image_url = article.get('image', '')

            if image_url not in unique_image_urls and favourite_team.lower() in title.lower():
               
                news_list.append({'title': title, 'description': description, 'url': url, 'image_url': image_url})
                unique_image_urls.add(image_url)
            
        cache.set(f'news_{search_query}', news_list, 86400)

        return news_list

def getfixtures(request):
    """
    Retrieves fixtures data from an external API.
    Updates match data if available.
    Sorts fixtures by gameweek and date.
    """
    user_profile = UserProfile.objects.get(user=request.user)
    current_season = get_current_season()
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"#
    querystring = {"league": "39", "season": current_season, "timezone": "Europe/London"}
    
    headers = {
        "X-RapidAPI-Key": FOOTBALL_API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    
    response = requests.get(url, headers=headers, params=querystring)
    
    data = response.json()

    fixtures_by_gameweek = {}

    for fixture in data['response']:
        gameweek = fixture['league']['round']
        fixture_status = fixture['fixture']['status']['short']
        
        if gameweek not in fixtures_by_gameweek:
            fixtures_by_gameweek[gameweek] = []

        home_team = fixture['teams']['home']['name']
        away_team = fixture['teams']['away']['name']
        home_score = fixture['goals']['home']
        away_score = fixture['goals']['away']
        home_logo = fixture['teams']['home']['logo']
        away_logo = fixture['teams']['away']['logo']
        fixture_id = fixture['fixture']['id']

        try:
            match = Match.objects.get(fixture_id=fixture_id)
            match.home_score = home_score
            match.away_score = away_score
            match.result = f"{home_score}:{away_score}"
            match.match_status = fixture_status
            match.save()
            
        except Match.DoesNotExist:
            match = Match.objects.create(
                team1=home_team,
                team2=away_team,
                home_score=home_score,
                away_score=away_score,
                result=f"{home_score}:{away_score}",
                fixture_id=fixture_id, 
                match_status=fixture_status,
            )
          
        fixtures_by_gameweek[gameweek].append({
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'home_logo': home_logo,
            'away_logo': away_logo,
            'fixture_date': (fixture['fixture']['date'])[0:10],
            'fixture_time': (fixture['fixture']['date'])[11:16],
            'fixture_id': fixture_id,
            'fixture_status': fixture_status 
        })

    for gameweek, fixtures in fixtures_by_gameweek.items():
        fixtures_by_gameweek[gameweek] = sorted(fixtures, key=itemgetter('fixture_date', 'fixture_time'))

    current_gameweek = get_current_gameweek(request)

    gameweek_number = int(current_gameweek.split('-')[-1].strip())

    offset = int(request.GET.get('offset', gameweek_number-1))
   
    selected_gameweek = list(fixtures_by_gameweek.keys())[offset]

    context = {
        'fixtures_by_gameweek': fixtures_by_gameweek,
        'user_profile': user_profile,
        'selected_gameweek': selected_gameweek,
        'offset': offset,
    }
   
    return context

@login_required(login_url='/')
def get_current_gameweek(request):
    """
    Retrieves the current gameweek from an external API.
    Caches the current gameweek for future use.
    """
    cached_gameweek = cache.get('current_gameweek')
    if cached_gameweek:
        return cached_gameweek
    current_season = get_current_season()
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures/rounds"
    querystring = {"league": "39", "season": current_season, "current": "true"}
    headers = {
        "X-RapidAPI-Key": FOOTBALL_API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    try:
        current_gameweek = response.json()['response'][0]
    except:
        current_gameweek="1"
    
   
    cache.set('current_gameweek', current_gameweek, timeout=86400)
    
    return current_gameweek

@login_required(login_url='/')
def fixtures(request):
    """
    Renders the fixtures page.
    Retrieves fixtures data.
    """
    context = getfixtures(request)
    fixtures_by_gameweek = context.get('fixtures_by_gameweek', [])
    selected_gameweek = context.get('selected_gameweek')
    offset = context.get('offset', 0)

    gameweeks = []
    for gameweek, fixtures in fixtures_by_gameweek.items():
        gameweek_data = {
            'gameweek_number': gameweek,
            'selected': gameweek == selected_gameweek,
            'fixtures': fixtures,
        }
        gameweeks.append(gameweek_data)

    user_profile = context.get('user_profile')

    return render(request, 'main/fixtures.html', {'gameweeks': gameweeks,'user_profile': user_profile,'offset': offset,})


@login_required(login_url='/')

def match_bet(request, home_team, away_team):
    """
    Handles the bet placement for a specific match.
    """
    user_profile = UserProfile.objects.get(user=request.user)
    data = getfixtures(request)
    
    fixtures_by_gameweek= data.get('fixtures_by_gameweek', [])

    fixture_id = None

    for gameweek, fixtures in fixtures_by_gameweek.items():
        for match in fixtures:
            if match['home_team'] == home_team and match['away_team'] == away_team:
                fixture_id = match['fixture_id']
                break
        if fixture_id:
            break
    fixture_odds = get_odds_from_api(fixture_id)
    
    try:
        Bet365_home_odds = ([odd['odd'] for odd in fixture_odds if odd['value'] == 'Home'][0])
        Bet365_draw_odds = ([odd['odd'] for odd in fixture_odds if odd['value'] == 'Draw'][0])
        Bet365_away_odds = ([odd['odd'] for odd in fixture_odds if odd['value'] == 'Away'][0])
    except IndexError:
        Bet365_home_odds = Bet365_away_odds = Bet365_draw_odds = None

    exact_score_odds = {f"{i}:{j}": None for i in range(5) for j in range(5)}
    for i in range(5):
        for j in range(5):
            try:
                exact_score_odds[f"{i}:{j}"] = ([odd['odd'] for odd in fixture_odds if odd['bet_name'] == 'Exact Score' and odd['value'] == f'{i}:{j}'][0])
            except IndexError:
                pass 
    
    context={
        'home_team': home_team,
        'away_team': away_team,
        'fixtures_by_gameweek':fixtures_by_gameweek,
        'user_profile': user_profile, 
        'Bet365_home': Bet365_home_odds,
        'Bet365_draw': Bet365_draw_odds,
        'Bet365_away': Bet365_away_odds,
        'betting_info_not_available': not bool(fixture_odds),
        'fixture_id': fixture_id, 
        'exact_score_odds' : exact_score_odds  
    }

    if request.method == 'POST':
        match = Match.objects.get(fixture_id=fixture_id)
        if 'winner_prediction' in request.POST:
            
            winner_prediction = request.POST.get('winner_prediction')
            winner_bet_amount = int(request.POST.get('winner_bet_amount'))

            if user_profile.points_balance >= winner_bet_amount:
                
                user_profile.points_balance -= winner_bet_amount
                user_profile.save()

                bet, created = Bet.objects.get_or_create(
                    user=request.user,
                    match=match,
                    bet_amount=winner_bet_amount,
                    bet_time=timezone.now(),
                    bet_type='Winner'
                )
                
                winner_bet, _ = WinnerBet.objects.get_or_create(
                    bet=bet,
                    winning_team=winner_prediction
                )
                if winner_prediction == home_team:
                    odds_for_winner_bet = Bet365_home_odds
                elif winner_prediction == away_team:
                    odds_for_winner_bet = Bet365_away_odds
                else:
                    odds_for_winner_bet = Bet365_draw_odds
                    
                if odds_for_winner_bet:
                    bet_return = int(winner_bet_amount+(winner_bet_amount * odds_for_winner_bet))
                    
                    bet.bet_return = bet_return
                    bet.save()

                
                messages.success(request, 'Winner prediction saved successfully.')
            else:
                messages.error(request, 'Insufficient points balance to place the bet.')


        elif 'home_score' in request.POST and 'away_score' in request.POST:
            
            home_score_prediction = int(request.POST.get('home_score'))
            away_score_prediction = int(request.POST.get('away_score'))
            score_bet_amount = int(request.POST.get('bet_amount'))
            score_prediction=f"{home_score_prediction}:{away_score_prediction}"

            

            if user_profile.points_balance >= score_bet_amount:
                
                user_profile.points_balance -= score_bet_amount
                user_profile.save() 

               
                bet, created = Bet.objects.get_or_create(
                    user=request.user,
                    match=match,
                    bet_amount=score_bet_amount,
                    bet_time=timezone.now(),
                    bet_type='Score'
                )

                
                score_bet, _ = ScoreBet.objects.get_or_create(
                    bet=bet,
                    home_team_score=home_score_prediction,
                    away_team_score=away_score_prediction,
                    score_prediction = score_prediction
                )
                any_other_score_odds=(home_score_prediction + away_score_prediction)*10
                odds_for_score_bet = exact_score_odds.get(score_prediction, Fraction(any_other_score_odds, 1))
                bet_return = int(score_bet_amount+(score_bet_amount * odds_for_score_bet))
                bet.bet_return = bet_return
                bet.save()
                    

            
                messages.success(request, 'Score predictions saved successfully.')
            else:
                messages.error(request, 'Insufficient points balance to place the bet.')
        
        user_profile.total_points_placed = Bet.objects.filter(user=request.user).aggregate(Sum('bet_amount'))['bet_amount__sum'] or 0
        user_profile.total_points_won = Bet.objects.filter(user=request.user, bet_status='won').aggregate(Sum('bet_return'))['bet_return__sum'] or 0
        if user_profile.total_points_placed!=0:
            user_profile.percentage_of_points_won=round((user_profile.total_points_won/user_profile.total_points_placed) *100, 2) 
        user_profile.save()

    bets_exist_for_match = Bet.objects.filter(user=request.user, match__fixture_id=fixture_id).exists()
    context['bets_exist_for_match']= bets_exist_for_match
    return render(request, 'main/match_bet.html', context)



def handle_winner_bets(request, user):
    """
    Handles the winner prediction bets for all matches.
    """
    for bet in Bet.objects.filter(user=user):
        match = bet.match
        if match.match_status == "FT" :
            if match.home_score > match.away_score:
                winner = match.team1
            elif match.home_score < match.away_score:
                winner = match.team2
            else:
                winner = "draw"
            if bet.bet_type == 'Winner'  and bet.bet_status == 'pending':
                winner_bet = WinnerBet.objects.get(bet=bet)
                if winner_bet.winning_team == winner:
                    
                    user_profile = UserProfile.objects.get(user=user)
                    user_profile.points_balance += bet.bet_return
                    user_profile.save()
                    bet.bet_status = 'won'
                    bet.save()
                    messages.success(request, f'Congratulations! You won the {bet.bet_type} bet for the match between {match.team1} and {match.team2} where you predicted {winner_bet.winning_team}. You have received {bet.bet_return} points.')
                else:
                    bet.bet_status = 'lost'
                    bet.save()
                    messages.error(request, f'Unfortunately, you lost the {bet.bet_type} bet for the match between {match.team1} and {match.team2} where you predicted {winner_bet.winning_team}.')

                    

def handle_score_prediction_bets(request, user):
    """
    Handles the score prediction bets for all matches.
    """
    for bet in Bet.objects.filter(user=user):
        match = bet.match
        if match.match_status == "FT" :
            actual_score= f"{match.home_score}:{match.away_score}"
            if bet.bet_type == 'Score'  and bet.bet_status == 'pending':
                score_bet = ScoreBet.objects.get(bet=bet)
                if score_bet.score_prediction == actual_score:
                    user_profile = UserProfile.objects.get(user=user)
                    user_profile.points_balance += bet.bet_return
                    user_profile.save()
                    bet.bet_status = 'won'
                    bet.save()
                    messages.success(request, f'Congratulations! You won the {bet.bet_type} bet for the match between {match.team1} and {match.team2} where you predicted {score_bet.score_prediction}. You have received {bet.bet_return} points.')
                else:
                    bet.bet_status = 'lost'
                    bet.save()
                    messages.error(request, f'Unfortunately, you lost the {bet.bet_type} bet for the match between {match.team1} and {match.team2} where you predicted {score_bet.score_prediction}.')


def decimal_to_fractional(decimal_odds):
    """
    Converts decimal odds to fractional odds.
    """

    if decimal_odds < 1:
        raise ValueError("Decimal odds must be greater than or equal to 1.")

    fractional_odds = Fraction(decimal_odds - 1).limit_denominator()
    
    return fractional_odds

def get_odds_from_api(fixture_id):
    """
    Retrieves odds for a specific match from API.
    """
    url = "https://api-football-v1.p.rapidapi.com/v3/odds"
    headers = {
        "X-RapidAPI-Key": FOOTBALL_API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    querystring = {"fixture": str(fixture_id)}
   
    response = requests.get(url, headers=headers, params=querystring)

    odds_data = response.json().get('response', [])

    fixture_odds = []

    for match in odds_data:
        if 'fixture' in match and 'id' in match['fixture'] and match['fixture']['id'] == fixture_id:
            for bookmaker in match.get('bookmakers', []):
                if bookmaker.get('name', '') == 'Bet365':
                    for bet in bookmaker.get('bets', []):
                        odd_values = bet.get('values', [])
                        for odd in odd_values:
                            fractional_odd = decimal_to_fractional(float(odd['odd']))
                            fixture_odds.append({
                                'bookmaker': 'Bet365',
                                'bet_name': bet['name'],
                                'value': odd['value'],
                                'odd': fractional_odd,
                                'multiplier_odd': odd['odd']
                            })
    return fixture_odds
 
@login_required(login_url='/')
def Pl_table(request):
    """
    Renders the Premier League table page.
    Retrieves the standings data from an external API
    """
    user_profile = UserProfile.objects.get(user=request.user)
    current_season = get_current_season()
    url = "https://api-football-v1.p.rapidapi.com/v3/standings"
    headers = {
        "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
        "x-rapidapi-key": FOOTBALL_API_KEY,
    }
    params = {
        "league": "39",  
        "season": current_season,  
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    table = data["response"][0]["league"]["standings"][0]
    
    return render(request, "main/table.html", {"table": table, 'user_profile': user_profile})

def get_current_season():
    current_year = datetime.now().year
    current_month = datetime.now().month
    if current_month >= 8:  
        return current_year
    else:
        return current_year - 1

def thread_list(request):
    """
    Returns a page listing all the threads
    """
    user_profile = UserProfile.objects.get(user=request.user)
    threads = Thread.objects.all()
    return render(request, 'main/thread_list.html', {'threads': threads, 'user_profile': user_profile})

def create_thread(request):
    """
    Handles the creation of a new thread.
    """
    user_profile = UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        title = request.POST.get('title')
        creator = request.user
        thread = Thread.objects.create(title=title, creator=creator)
        return redirect('thread_detail', thread_id=thread.id)
    return render(request, 'main/create_thread.html', {'user_profile': user_profile})

def thread_detail(request, thread_id):
    """
    Renders the detail page for a specific thread.
    """
    user_profile = UserProfile.objects.get(user=request.user)
    thread = Thread.objects.get(pk=thread_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        sender = request.user
        Message.objects.create(thread=thread, sender=sender, content=content)
        return redirect('thread_detail', thread_id=thread_id)
    return render(request, 'main/thread_detail.html', {'thread': thread, 'user_profile': user_profile})

def delete_message(request, thread_id, message_id):
    """
    Handles the deletion of a message within a thread
    """
    message = Message.objects.get(pk=message_id)
    if request.user == message.sender:
        message.delete()
        return redirect('thread_detail', thread_id=thread_id)
    
def delete_thread(request, thread_id):
    """
    Handles the deletion of a thread
    """
    thread = Thread.objects.get(pk=thread_id)
    if request.user == thread.creator:
        thread.delete()
        return redirect('thread_list')  