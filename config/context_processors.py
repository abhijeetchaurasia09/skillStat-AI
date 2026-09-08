from django.conf import settings

def app_context(request):
    """
    Global template context processor for SkillStat AI.
    Provides current AI mode, system name, and platform metadata.
    """
    return {
        'PLATFORM_NAME': 'SkillStat AI',
        'PLATFORM_TAGLINE': 'Intelligent Competency & Personalized Learning Platform',
        'AI_MODE': getattr(settings, 'AI_MODE', 'mock'),
        'AI_MODEL': getattr(settings, 'AI_MODEL', 'gemini-1.5-flash'),
        'HAS_REAL_AI': bool(getattr(settings, 'AI_API_KEY', '').strip()),
    }
