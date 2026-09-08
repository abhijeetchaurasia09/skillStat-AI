from competency.models import UserCompetency, Skill
from .models import Course, Recommendation

class RecommendationService:
    """
    Personalized Recommendation & Explainable AI Engine.
    Identifies user competency gaps and generates tailored course recommendations
    along with clear, transparent explanations for why each course was suggested.
    """

    @classmethod
    def generate_recommendations_for_user(cls, user):
        """
        Scans all user competencies, detects gaps, and generates explainable recommendations.
        """
        competencies = UserCompetency.objects.filter(user=user).select_related('skill')
        created_or_updated = []

        for comp in competencies:
            skill = comp.skill
            gap = comp.gap
            priority = comp.priority

            courses = Course.objects.filter(skill=skill, is_active=True)
            for course in courses:
                # Build transparent pedagogical explanation
                if gap > 0:
                    reason = (
                        f"You scored {comp.current_level:.1f}% in {skill.name} while the target "
                        f"competency is {skill.required_level}%, resulting in a {gap:.1f}-point gap. "
                        f"Therefore, '{course.title}' has been marked {priority} PRIORITY to help you "
                        f"master {skill.name} and close this proficiency gap."
                    )
                else:
                    reason = (
                        f"Your competency in {skill.name} is at {comp.current_level:.1f}%, exceeding or "
                        f"meeting the required threshold of {skill.required_level}%. This course is recommended "
                        f"as an optional mastery module to maintain high proficiency."
                    )

                rec, created = Recommendation.objects.update_or_create(
                    user=user,
                    course=course,
                    defaults={
                        'skill': skill,
                        'priority': priority,
                        'reason': reason,
                        'gap_points': gap,
                        'is_completed': False,
                    }
                )
                created_or_updated.append(rec)

        return created_or_updated

    @classmethod
    def get_personalized_learning_path(cls, user):
        """
        Generates an ordered learning roadmap based on highest gap priorities (HIGH -> MEDIUM -> LOW).
        """
        # Ensure fresh recommendations
        recs = Recommendation.objects.filter(user=user, is_completed=False).select_related('course', 'skill', 'course__skill').order_by(
            '-gap_points', 'course__title'
        )
        if not recs.exists():
            cls.generate_recommendations_for_user(user)
            recs = Recommendation.objects.filter(user=user, is_completed=False).select_related('course', 'skill', 'course__skill').order_by(
                '-gap_points', 'course__title'
            )
        return recs


class IGOTIntegrationService:
    """
    Architecture Abstraction for iGOT Karmayogi National Portal Integration.
    Designed for SIH 2026 PS26101 compliance.
    
    Distinguishes clearly between Prototype Simulated Mode and Production Authorized API Mode.
    Provides data contracts and adapter methods for competency framework mapping.
    """

    INTEGRATION_MODE = "PROTOTYPE" # 'PROTOTYPE' or 'AUTHORIZED_API'
    IGOT_API_BASE_URL = "https://karmayogi.nic.in/api/v1" # Target official endpoint

    @classmethod
    def get_connection_status(cls):
        return {
            "status": "Ready for National Gateway Hook",
            "integration_mode": cls.INTEGRATION_MODE,
            "ecosystem": "iGOT Karmayogi (DoPT / MoSPI National Competency Framework)",
            "gateway_type": "REST / OAuth 2.0 Mutual TLS (mTLS) Adapter",
            "notes": "Running in Prototype Integration mode for SIH 2026. Data structures conform to National Competency Passbook specs."
        }

    @classmethod
    def map_to_igot_competency(cls, skill_name, score):
        """
        Maps SkillStat AI competencies to Karmayogi Competency Dictionary standard.
        """
        mapping = {
            'Statistics': {'igot_code': 'COMP-STAT-001', 'domain': 'Domain Competency - Statistical Governance'},
            'Python': {'igot_code': 'COMP-TECH-014', 'domain': 'Technical Competency - Computational Analytics'},
            'Data Analysis': {'igot_code': 'COMP-ANAL-007', 'domain': 'Domain Competency - Evidence-Based Decision Making'},
            'Data Visualization': {'igot_code': 'COMP-VIS-003', 'domain': 'Behavioral & Functional - Visual Communication'},
            'Regression': {'igot_code': 'COMP-STAT-009', 'domain': 'Domain Competency - Predictive Statistical Modeling'},
            'Survey Methodology': {'igot_code': 'COMP-SURV-002', 'domain': 'Domain Competency - Field Survey & Sampling Design'},
            'Statistical Interpretation': {'igot_code': 'COMP-INTP-005', 'domain': 'Functional Competency - Policy Analytics'},
        }
        meta = mapping.get(skill_name, {'igot_code': 'COMP-GEN-099', 'domain': 'General Competency'})
        return {
            'skill_name': skill_name,
            'score': score,
            'igot_code': meta['igot_code'],
            'domain': meta['domain'],
            'sync_eligible': True,
        }

    @classmethod
    def sync_user_competencies_to_igot(cls, user, competencies):
        """
        Simulates two-way sync with iGOT Karmayogi user digital profile passbook.
        """
        synced_records = []
        for comp in competencies:
            mapped = cls.map_to_igot_competency(comp.skill.name, comp.current_level)
            synced_records.append({
                'user': user.username,
                'competency_code': mapped['igot_code'],
                'skill': mapped['skill_name'],
                'proficiency_level': mapped['score'],
                'status': 'Synchronized (Prototype Pipeline)',
            })
        return {
            'success': True,
            'timestamp': '2026-09-07T12:00:00Z',
            'synced_count': len(synced_records),
            'records': synced_records,
            'mode': 'Prototype Integration Layer'
        }
