from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Assessment, AssessmentAttempt, UserCompetency, Skill
from .services import CompetencyService
from learning.services import RecommendationService

@login_required
def assessment_detail_view(request):
    """
    Renders the active diagnostic assessment and questions for the user to take.
    """
    assessment = Assessment.objects.filter(is_active=True).first()
    if not assessment:
        messages.error(request, "No active diagnostic assessment is currently configured.")
        return redirect('dashboard:index')

    questions = assessment.questions.all().select_related('skill')
    
    # Check if user has taken it before
    last_attempt = AssessmentAttempt.objects.filter(user=request.user, assessment=assessment).first()

    return render(request, 'competency/assessment_take.html', {
        'assessment': assessment,
        'questions': questions,
        'total_questions': questions.count(),
        'last_attempt': last_attempt,
    })


@login_required
def assessment_submit_view(request):
    """
    Processes the submitted diagnostic assessment answers.
    Evaluates answers, updates competencies, calculates skill gaps, and triggers explainable recommendations.
    """
    if request.method != 'POST':
        return redirect('competency:assessment')

    assessment_id = request.POST.get('assessment_id')
    assessment = get_object_or_404(Assessment, id=assessment_id)

    # Gather answers from POST
    answers = {}
    for key, value in request.POST.items():
        if key.startswith('question_'):
            q_id = key.replace('question_', '')
            answers[q_id] = value

    if not answers:
        messages.warning(request, "Please select answers for the assessment before submitting.")
        return redirect('competency:assessment')

    try:
        attempt = CompetencyService.evaluate_assessment_submission(
            user=request.user,
            assessment=assessment,
            submitted_answers=answers
        )
        messages.success(request, f"Assessment completed! You scored {attempt.score_percentage:.1f}%. Your competency scores have been updated.")
        return redirect('competency:assessment_result', attempt_id=attempt.id)
    except Exception as e:
        messages.error(request, f"Error processing assessment: {str(e)}")
        return redirect('competency:assessment')


@login_required
def assessment_result_view(request, attempt_id):
    """
    Renders diagnostic assessment attempt results with question-by-question breakdown,
    correct explanations, and link to updated skill gaps.
    """
    attempt = get_object_or_404(AssessmentAttempt, id=attempt_id, user=request.user)
    answers = attempt.answers.all().select_related('question', 'question__skill')

    # Calculate skill performance in this attempt
    skill_breakdown = {}
    for ans in answers:
        s_name = ans.question.skill.name
        if s_name not in skill_breakdown:
            skill_breakdown[s_name] = {'total': 0, 'correct': 0}
        skill_breakdown[s_name]['total'] += 1
        if ans.is_correct:
            skill_breakdown[s_name]['correct'] += 1

    for s_name, data in skill_breakdown.items():
        data['percentage'] = round((data['correct'] / data['total']) * 100, 1)

    return render(request, 'competency/assessment_result.html', {
        'attempt': attempt,
        'answers': answers,
        'skill_breakdown': skill_breakdown,
    })


@login_required
def skill_gaps_view(request):
    """
    Dedicated view displaying user's current competency scores, target required scores,
    calculated gaps, and priority levels (HIGH, MEDIUM, LOW).
    """
    skill_gaps = CompetencyService.get_skill_gaps(request.user)
    overall_score = CompetencyService.calculate_overall_competency(request.user)
    
    high_count = sum(1 for g in skill_gaps if g['priority'] == 'HIGH')
    med_count = sum(1 for g in skill_gaps if g['priority'] == 'MEDIUM')
    low_count = sum(1 for g in skill_gaps if g['priority'] == 'LOW')

    return render(request, 'competency/skill_gaps.html', {
        'skill_gaps': skill_gaps,
        'overall_score': overall_score,
        'high_count': high_count,
        'med_count': med_count,
        'low_count': low_count,
    })
