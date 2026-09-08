from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    path('', views.quiz_list_view, name='quiz_list'),
    path('generate/', views.ai_quiz_generate_view, name='ai_generate'),
    path('<int:quiz_id>/', views.quiz_take_view, name='quiz_take'),
    path('<int:quiz_id>/submit/', views.quiz_submit_view, name='quiz_submit'),
    path('attempt/<int:attempt_id>/', views.quiz_result_view, name='quiz_result'),
]
