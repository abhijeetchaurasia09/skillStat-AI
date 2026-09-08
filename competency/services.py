from django.db import transaction
from .models import Skill, UserCompetency, Assessment, AssessmentQuestion, AssessmentAttempt, UserAnswer

class CompetencyService:
    """
    Core engine for computing user competencies, calculating skill gaps,
    and evaluating assessment submissions.
    """

    @staticmethod
    def ensure_user_competencies(user):
        """
        Ensures that a UserCompetency record exists for every active Skill in the system.
        """
        skills = Skill.objects.all()
        for skill in skills:
            UserCompetency.objects.get_or_create(
                user=user,
                skill=skill,
                defaults={'current_level': 0.0}
            )
        return UserCompetency.objects.filter(user=user).select_related('skill')

    @classmethod
    def get_user_competencies(cls, user):
        """
        Returns all UserCompetency records for the user.
        """
        cls.ensure_user_competencies(user)
        return UserCompetency.objects.filter(user=user).select_related('skill').order_by('-current_level')

    @classmethod
    def calculate_overall_competency(cls, user):
        """
        Returns average competency percentage across all skills.
        """
        competencies = cls.get_user_competencies(user)
        if not competencies:
            return 0.0
        total = sum(c.current_level for c in competencies)
        return round(total / competencies.count(), 1)

    @classmethod
    def get_skill_gaps(cls, user):
        """
        Calculates skill gaps for the user:
        gap = required_level - current_level
        Priority:
        gap >= 40 -> HIGH
        gap >= 20 -> MEDIUM
        gap < 20  -> LOW
        """
        competencies = cls.get_user_competencies(user)
        gaps = []
        for comp in competencies:
            gap_val = comp.gap
            gaps.append({
                'skill': comp.skill,
                'current_level': comp.current_level,
                'required_level': comp.skill.required_level,
                'gap': gap_val,
                'priority': comp.priority,
                'priority_badge': comp.priority_badge_class,
                'last_assessed': comp.last_assessed_at,
            })
        # Sort primarily by gap descending (largest gap first)
        gaps.sort(key=lambda x: x['gap'], reverse=True)
        return gaps

    @classmethod
    def evaluate_assessment_submission(cls, user, assessment, submitted_answers):
        """
        Evaluates submitted answers from a diagnostic assessment.
        submitted_answers: dict mapping question_id (int or str) -> chosen option ('A', 'B', 'C', 'D')

        Calculates:
        1. Overall score
        2. Skill-wise scores
        3. Updates UserCompetency table
        4. Calls RecommendationService to refresh recommendations
        """
        questions = assessment.questions.all().select_related('skill')
        total_questions = questions.count()
        if total_questions == 0:
            raise ValueError("This assessment has no questions.")

        correct_count = 0
        skill_counts = {} # skill_id -> {'total': 0, 'correct': 0, 'skill': Skill}

        for q in questions:
            sid = q.skill_id
            if sid not in skill_counts:
                skill_counts[sid] = {'total': 0, 'correct': 0, 'skill': q.skill}
            skill_counts[sid]['total'] += 1

            selected = submitted_answers.get(str(q.id)) or submitted_answers.get(q.id)
            if selected and selected.strip().upper() == q.correct_option.strip().upper():
                correct_count += 1
                skill_counts[sid]['correct'] += 1

        score_pct = round((correct_count / total_questions) * 100.0, 1)

        with transaction.atomic():
            attempt = AssessmentAttempt.objects.create(
                user=user,
                assessment=assessment,
                total_questions=total_questions,
                correct_answers=correct_count,
                score_percentage=score_pct
            )

            # Record individual answers
            for q in questions:
                selected = submitted_answers.get(str(q.id)) or submitted_answers.get(q.id) or ''
                selected_clean = selected.strip().upper()
                is_correct = (selected_clean == q.correct_option.strip().upper())
                UserAnswer.objects.create(
                    attempt=attempt,
                    question=q,
                    selected_option=selected_clean,
                    is_correct=is_correct
                )

            # Update competency scores per skill tested
            for sid, stats in skill_counts.items():
                skill_pct = round((stats['correct'] / stats['total']) * 100.0, 1)
                comp, created = UserCompetency.objects.get_or_create(
                    user=user,
                    skill=stats['skill'],
                    defaults={'current_level': skill_pct, 'assessment_count': 1}
                )
                if not created:
                    # Blend previous competency with new assessment
                    # 40% historical weight + 60% new assessment
                    if comp.assessment_count == 0 or comp.current_level == 0.0:
                        comp.current_level = skill_pct
                    else:
                        comp.current_level = round((comp.current_level * 0.4) + (skill_pct * 0.6), 1)
                    comp.assessment_count += 1
                    comp.save()

            # Refresh personalized explainable recommendations
            from learning.services import RecommendationService
            RecommendationService.generate_recommendations_for_user(user)

        return attempt
