from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='index'),
    path('progress/', views.progress_view, name='progress'),
    path('api/competency/', views.competency_api_view, name='api_competency'),
    path('sync-igot/', views.igot_sync_action_view, name='sync_igot'),
]
