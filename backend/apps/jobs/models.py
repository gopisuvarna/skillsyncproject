# """Job model for Adzuna real-time ingestion."""
# import uuid
# from django.db import models


# class Job(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     external_id = models.CharField(max_length=256, unique=True, db_index=True)
#     title = models.CharField(max_length=512)
#     company = models.CharField(max_length=256, blank=True)
#     location = models.CharField(max_length=256, blank=True)
#     description = models.TextField(blank=True)
#     url = models.URLField(max_length=1024, blank=True)
#     salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
#     salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)


# class JobSkill(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='skills')
#     skill = models.ForeignKey('skills.Skill', on_delete=models.CASCADE, related_name='job_skills')
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('job', 'skill')


"""Job model for Adzuna real-time ingestion."""
import uuid
from django.db import models


class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.CharField(max_length=256, unique=True, db_index=True)
    title = models.CharField(max_length=512)
    company = models.CharField(max_length=256, blank=True)
    location = models.CharField(max_length=256, blank=True)
    description = models.TextField(blank=True)
    url = models.URLField(max_length=1024, blank=True)
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class JobSkill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey('skills.Skill', on_delete=models.CASCADE, related_name='job_skills')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'skill')


class UserRoleCache(models.Model):
    """
    Stores pre-computed skill-to-role matches for a user.
    Populated by trigger_role_matching() on login (background thread).
    Read by recommendations + analytics views for instant response.
    """
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='role_cache',
    )
    # JSON list of ranked role dicts — same shape as top_roles API response
    roles      = models.TextField(default='[]')
    updated_at = models.DateTimeField(auto_now=True)

    def get_roles(self):
        import json
        try:
            return json.loads(self.roles)
        except Exception:
            return []

    def __str__(self):
        return f"RoleCache(user={self.user_id}, updated={self.updated_at})"