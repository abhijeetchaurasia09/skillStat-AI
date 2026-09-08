from django.urls import path
from . import views

app_name = 'competency'

urlpatterns = [
    path('assessment/', views.assessment_detail_view, name='assessment'),
    path('assessment/submit/', views.assessment_submit_view, name='assessment_submit'),
    path('assessment/result/<int:attempt_id>/', views.assessment_result_view, name='assessment_result'),
    path('gaps/', views.skill_gaps_view, name='skill_gaps'),
]
