from django.db import transaction
from competency.models import Skill, UserCompetency
from learning.services import RecommendationService
from .models import Quiz, QuizQuestion, QuizAttempt, QuizUserAnswer

class QuizService:
    """
    Manages quiz creation from AI/PDF pipelines, evaluation of attempts,
    and adaptive, explainable closed-loop competency updates.
    """

    @classmethod
    def create_quiz_from_mcqs(cls, user, title, questions_data, material=None, skill=None, difficulty='Intermediate', ai_mode='mock'):
        """
        Takes validated MCQ question dictionaries and persists them as a playable Quiz.
        """
        with transaction.atomic():
            quiz = Quiz.objects.create(
                user=user,
                title=title,
                material=material,
                skill=skill,
                difficulty=difficulty,
                source_type='uploaded_pdf' if material else 'ai_generated',
                is_ai_generated=True,
                ai_mode_used=ai_mode
            )

            for q in questions_data:
                # Resolve skill for question if specified
                q_skill = skill
                skill_name = q.get('skill')
                if skill_name:
                    found_skill = Skill.objects.filter(name__iexact=skill_name).first()
                    if found_skill:
                        q_skill = found_skill

                QuizQuestion.objects.create(
                    quiz=quiz,
                    skill=q_skill,
                    question_text=q['question'],
                    option_a=q['option_a'],
                    option_b=q['option_b'],
                    option_c=q['option_c'],
                    option_d=q['option_d'],
                    correct_option=q['correct_option'],
                    explanation=q.get('explanation', ''),
                    difficulty=q.get('difficulty', difficulty)
                )

        return quiz

    @classmethod
    def evaluate_quiz_submission(cls, user, quiz, user_answers_dict):
        """
        Evaluates a user's answers for a quiz attempt, calculates score,
        updates competency score dynamically with an explainable algorithm,
        and records before/after metrics.
        """
        questions = quiz.questions.all().select_related('skill')
        total_questions = questions.count()
        if total_questions == 0:
            raise ValueError("This quiz has no questions.")

        correct_count = 0
        for q in questions:
            chosen = (user_answers_dict.get(str(q.id)) or user_answers_dict.get(q.id) or '').strip().upper()
            if chosen == q.correct_option.strip().upper():
                correct_count += 1

        score_pct = round((correct_count / total_questions) * 100.0, 1)

        # Determine target skill for competency update
        target_skill = quiz.skill
        if not target_skill:
            # Pick most frequent skill in questions or fallback to first
            skills_in_q = [q.skill for q in questions if q.skill]
            if skills_in_q:
                target_skill = max(set(skills_in_q), key=skills_in_q.count)
            else:
                target_skill = Skill.objects.first()

        # Retrieve current baseline competency
        comp, created = UserCompetency.objects.get_or_create(
            user=user,
            skill=target_skill,
            defaults={'current_level': 0.0}
        )
        before_competency = comp.current_level

        # Calculate explainable competency increment
        # Simple weighted formula:
        # If quiz score > before_competency: gain = (score_pct - before_competency) * 0.35
        # If score is lower but >= 50%: modest practice gain = +2.0%
        # If score is low (< 50%): score is not degraded harshly to encourage learning (gain = 0.0)
        if score_pct > before_competency:
            competency_gain = round((score_pct - before_competency) * 0.35, 1)
        elif score_pct >= 50.0:
            competency_gain = round(min(5.0, score_pct * 0.04), 1)
        else:
            competency_gain = 0.0

        after_competency = min(100.0, round(before_competency + competency_gain, 1))

        with transaction.atomic():
            attempt = QuizAttempt.objects.create(
                user=user,
                quiz=quiz,
                total_questions=total_questions,
                correct_answers=correct_count,
                score_percentage=score_pct,
                before_competency=before_competency,
                after_competency=after_competency,
                competency_gain=competency_gain
            )

            for q in questions:
                chosen = (user_answers_dict.get(str(q.id)) or user_answers_dict.get(q.id) or '').strip().upper()
                is_correct = (chosen == q.correct_option.strip().upper())
                QuizUserAnswer.objects.create(
                    attempt=attempt,
                    question=q,
                    selected_option=chosen,
                    is_correct=is_correct
                )

            # Update UserCompetency
            comp.current_level = after_competency
            comp.assessment_count += 1
            comp.save()

            # Refresh explainable recommendations immediately
            RecommendationService.generate_recommendations_for_user(user)

        return attempt
