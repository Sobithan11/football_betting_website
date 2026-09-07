from django.urls import path
from . import views


urlpatterns = [
path("fixtures/", views.fixtures, name="fixtures"),
path("table/", views.Pl_table, name="PLtable"),
path("home/", views.home, name="home"),
path('match_bet/<str:home_team>/<str:away_team>/', views.match_bet, name='match_bet'),
path('select-favourite-team/', views.select_favourite_team, name='select_favourite_team'),
path('bet_history/', views.bet_history, name='bet_history'),
path('leaderboard/', views.leaderboard, name='leaderboard'),
path('threads/', views.thread_list, name='thread_list'),
path('threads/create/', views.create_thread, name='create_thread'),
path('threads/<int:thread_id>/', views.thread_detail, name='thread_detail'),
path('threads/<int:thread_id>/delete_message/<int:message_id>/', views.delete_message, name='delete_message'),
path('threads/<int:thread_id>/delete/', views.delete_thread, name='delete_thread'),
]