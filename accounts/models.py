from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    """
    Profile extension for Django User representing employee/learner metadata.
    Designed for civil servants, statistical officers, and public servants (iGOT Karmayogi alignment).
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    department = models.CharField(max_length=150, default='Ministry of Statistics & Programme Implementation (MoSPI)')
    job_role = models.CharField(max_length=150, default='Statistical Officer / Data Analyst')
    bio = models.TextField(blank=True, default='Passionate about statistical analysis, data-driven governance, and policy analytics.')
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({self.job_role})"

@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            UserProfile.objects.create(user=instance)
