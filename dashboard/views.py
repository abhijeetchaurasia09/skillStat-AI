from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from competency.models import UserCompetency, Skill, AssessmentAttempt
from competency.services import CompetencyService
from learning.models import Recommendation, Course
from learning.services import RecommendationService, IGOTIntegrationService
from quizzes.models import QuizAttempt

@login_required
def dashboard_view(request):
    """
    Main executive learner dashboard.
    Displays overall competency, skill scores, detected skill gaps,
    explainable AI recommendations, recent quiz performance, and Chart.js visualizations.
    """
    # Ensure user has initialized competencies and recommendations
    CompetencyService.ensure_user_competencies(request.user)
    competencies = CompetencyService.get_user_competencies(request.user)
    overall_score = CompetencyService.calculate_overall_competency(request.user)
    skill_gaps = CompetencyService.get_skill_gaps(request.user)

    # Top priority gaps
    high_gaps = [g for g in skill_gaps if g['priority'] == 'HIGH']
    medium_gaps = [g for g in skill_gaps if g['priority'] == 'MEDIUM']

    # Explainable recommendations
    recommendations = Recommendation.objects.filter(user=request.user, is_completed=False).select_related('course', 'skill')[:5]
    if not recommendations.exists():
        RecommendationService.generate_recommendations_for_user(request.user)
        recommendations = Recommendation.objects.filter(user=request.user, is_completed=False).select_related('course', 'skill')[:5]

    # Recent quiz attempts
    recent_quizzes = QuizAttempt.objects.filter(user=request.user).select_related('quiz')[:5]

    # Recent diagnostic assessment attempt
    last_assessment = AssessmentAttempt.objects.filter(user=request.user).first()

    # iGOT connection metadata
    igot_info = IGOTIntegrationService.get_connection_status()

    # Pre-format chart data for inline JSON injection into Chart.js
    chart_labels = [c.skill.name for c in competencies]
    chart_current_levels = [c.current_level for c in competencies]
    chart_required_levels = [c.skill.required_level for c in competencies]
    chart_gaps = [c.gap for c in competencies]

    context = {
        'overall_score': overall_score,
        'competencies': competencies,
        'skill_gaps': skill_gaps,
        'high_gaps_count': len(high_gaps),
        'medium_gaps_count': len(medium_gaps),
        'recommendations': recommendations,
        'recent_quizzes': recent_quizzes,
        'last_assessment': last_assessment,
        'igot_info': igot_info,
        'chart_labels': chart_labels,
        'chart_current_levels': chart_current_levels,
        'chart_required_levels': chart_required_levels,
        'chart_gaps': chart_gaps,
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def progress_view(request):
    """
    Dedicated analytics and competency trajectory view.
    """
    competencies = CompetencyService.get_user_competencies(request.user)
    overall_score = CompetencyService.calculate_overall_competency(request.user)
    quiz_attempts = QuizAttempt.objects.filter(user=request.user).order_by('completed_at')
    assessment_attempts = AssessmentAttempt.objects.filter(user=request.user).order_by('completed_at')

    # Data for historical timeline
    timeline_labels = [q.completed_at.strftime('%b %d, %H:%M') for q in quiz_attempts]
    timeline_scores = [q.score_percentage for q in quiz_attempts]
    timeline_competency = [q.after_competency for q in quiz_attempts]

    context = {
        'competencies': competencies,
        'overall_score': overall_score,
        'quiz_attempts': quiz_attempts.reverse()[:10],
        'assessment_attempts': assessment_attempts.reverse()[:5],
        'timeline_labels': timeline_labels,
        'timeline_scores': timeline_scores,
        'timeline_competency': timeline_competency,
        'total_quizzes_taken': quiz_attempts.count(),
    }
    return render(request, 'dashboard/progress.html', context)


@login_required
def competency_api_view(request):
    """
    JSON API endpoint returning live competency dataset for asynchronous Chart.js re-renders.
    """
    competencies = CompetencyService.get_user_competencies(request.user)
    data = {
        'labels': [c.skill.name for c in competencies],
        'current_scores': [c.current_level for c in competencies],
        'required_scores': [c.skill.required_level for c in competencies],
        'gaps': [c.gap for c in competencies],
        'overall_score': CompetencyService.calculate_overall_competency(request.user),
    }
    return JsonResponse(data)


@login_required
def igot_sync_action_view(request):
    """
    Triggers simulated two-way sync with the national iGOT Karmayogi digital passbook.
    """
    if request.method == 'POST':
        competencies = CompetencyService.get_user_competencies(request.user)
        sync_result = IGOTIntegrationService.sync_user_competencies_to_igot(request.user, competencies)
        messages.success(
            request,
            f"[iGOT Karmayogi Prototype Sync] Successfully dispatched {sync_result['synced_count']} "
            f"competency records to National Competency Passbook endpoint! (Status: 200 OK Simulated)"
        )
        return redirect('dashboard:index')
    return redirect('dashboard:index')
