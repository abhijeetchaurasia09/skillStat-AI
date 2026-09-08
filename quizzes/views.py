from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Quiz, QuizQuestion, QuizAttempt
from .services import QuizService
from learning.models import LearningMaterial
from competency.models import Skill
from ai_engine.services import AIService

@login_required
def quiz_list_view(request):
    """
    Lists available quizzes and past attempt history.
    """
    quizzes = Quiz.objects.all().select_related('skill', 'material', 'user')
    user_attempts = QuizAttempt.objects.filter(user=request.user).select_related('quiz')

    return render(request, 'quizzes/quiz_list.html', {
        'quizzes': quizzes,
        'user_attempts': user_attempts,
    })


@login_required
def ai_quiz_generate_view(request):
    """
    Interactive AI Quiz Generator.
    Extracts text from an uploaded material or accepts text,
    calls the AIService layer, creates a persistent Quiz, and redirects to take the quiz.
    """
    materials = LearningMaterial.objects.filter(extraction_status='success')
    skills = Skill.objects.all()

    preselected_material_id = request.GET.get('material_id')
    preselected_material = None
    if preselected_material_id:
        preselected_material = LearningMaterial.objects.filter(id=preselected_material_id).first()

    if request.method == 'POST':
        material_id = request.POST.get('material_id')
        skill_id = request.POST.get('skill_id')
        difficulty = request.POST.get('difficulty', 'Intermediate')
        num_questions = int(request.POST.get('num_questions', 5))
        custom_text = request.POST.get('custom_text', '').strip()

        material = None
        text_source = ""
        skill = None

        if material_id:
            material = get_object_or_404(LearningMaterial, id=material_id)
            text_source = material.extracted_text
            skill = material.skill

        if not text_source and custom_text:
            text_source = custom_text

        if skill_id:
            skill = Skill.objects.filter(id=skill_id).first() or skill

        skill_hint = skill.name if skill else None

        # Check sufficiency of text
        if not text_source or len(text_source.split()) < 30:
            messages.error(
                request,
                "Not enough learning material to reliably generate questions. "
                "Please choose a document with extractable text or provide at least 30 words of curriculum text."
            )
            return render(request, 'quizzes/ai_generate.html', {
                'materials': materials,
                'skills': skills,
                'preselected_material': material,
            })

        # Call AI service layer
        ai_res = AIService.generate_mcqs(
            text=text_source,
            number_of_questions=num_questions,
            difficulty=difficulty,
            skill_hint=skill_hint
        )

        if not ai_res.get('success') or not ai_res.get('questions'):
            messages.error(request, f"AI generation could not complete: {ai_res.get('message', 'Unknown error')}")
            return render(request, 'quizzes/ai_generate.html', {
                'materials': materials,
                'skills': skills,
                'preselected_material': material,
            })

        # Save to database
        title = f"AI Quiz: {material.title if material else (skill.name if skill else 'Competency Practice')}"
        if len(title) > 200:
            title = title[:197] + "..."

        quiz = QuizService.create_quiz_from_mcqs(
            user=request.user,
            title=title,
            questions_data=ai_res['questions'],
            material=material,
            skill=skill,
            difficulty=difficulty,
            ai_mode=ai_res.get('ai_mode_used', 'mock')
        )

        if ai_res.get('is_demo_mode'):
            messages.info(request, f"Quiz generated successfully in Demo Mode ({len(ai_res['questions'])} questions).")
        else:
            messages.success(request, f"Quiz generated successfully via {ai_res.get('ai_mode_used')} AI ({len(ai_res['questions'])} questions).")

        return redirect('quizzes:quiz_take', quiz_id=quiz.id)

    return render(request, 'quizzes/ai_generate.html', {
        'materials': materials,
        'skills': skills,
        'preselected_material': preselected_material,
    })


@login_required
def quiz_take_view(request, quiz_id):
    """
    Interactive test interface for taking a quiz.
    """
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()

    if questions.count() == 0:
        messages.warning(request, "This quiz currently has no questions.")
        return redirect('quizzes:quiz_list')

    return render(request, 'quizzes/quiz_take.html', {
        'quiz': quiz,
        'questions': questions,
        'total_questions': questions.count(),
    })


@login_required
def quiz_submit_view(request, quiz_id):
    """
    Evaluates quiz submission, updates user competency dynamically, and redirects to result.
    """
    if request.method != 'POST':
        return redirect('quizzes:quiz_take', quiz_id=quiz_id)

    quiz = get_object_or_404(Quiz, id=quiz_id)

    user_answers = {}
    for key, val in request.POST.items():
        if key.startswith('question_'):
            q_id = key.replace('question_', '')
            user_answers[q_id] = val

    if not user_answers:
        messages.warning(request, "Please select answers before submitting your quiz.")
        return redirect('quizzes:quiz_take', quiz_id=quiz_id)

    try:
        attempt = QuizService.evaluate_quiz_submission(
            user=request.user,
            quiz=quiz,
            user_answers_dict=user_answers
        )
        messages.success(
            request,
            f"Quiz completed! You scored {attempt.score_percentage:.1f}%. "
            f"Competency updated from {attempt.before_competency:.1f}% to {attempt.after_competency:.1f}% (+{attempt.competency_gain:.1f}% gain)!"
        )
        return redirect('quizzes:quiz_result', attempt_id=attempt.id)
    except Exception as e:
        messages.error(request, f"Error processing quiz: {str(e)}")
        return redirect('quizzes:quiz_take', quiz_id=quiz_id)


@login_required
def quiz_result_view(request, attempt_id):
    """
    Detailed review page showing final score, before/after competency gain,
    and question-by-question explanations.
    """
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    user_answers = attempt.user_answers.all().select_related('question')

    return render(request, 'quizzes/quiz_result.html', {
        'attempt': attempt,
        'quiz': attempt.quiz,
        'user_answers': user_answers,
    })
