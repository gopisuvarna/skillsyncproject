# """
# Job ingestion service: fetch from Adzuna, store in DB, extract skills,
# and upsert Role + RoleSkill rows so the recommendation engine stays fresh.

# Flow for every new job:
#   1. Save Job row
#   2. Extract skills via spaCy (no LLM — zero token cost)
#   3. Save Skill + JobSkill rows
#   4. Upsert Role row using the search keyword as the canonical role title
#   5. Upsert RoleSkill rows — importance weight based on skill position in list
# """
# import logging
# from datetime import timedelta

# from django.db import transaction
# from django.utils import timezone

# from core.services.adzuna_service import fetch_jobs
# from apps.skills.services import extract_skills, normalize_skill
# from apps.jobs.models import Job, JobSkill
# from apps.skills.models import Skill
# from apps.roles.models import Role, RoleSkill

# logger = logging.getLogger(__name__)


# # ── helpers ──────────────────────────────────────────────────────────────────

# def _get_or_create_skill(name: str) -> Skill:
#     nm = normalize_skill(name)
#     skill, _ = Skill.objects.get_or_create(
#         normalized_name=nm.lower(),
#         defaults={"name": nm},
#     )
#     return skill


# def _importance_weight(index: int, total: int) -> float:
#     """
#     Skills extracted earlier in the job text tend to be more prominent.
#     Top third → 1.0, middle third → 0.75, bottom third → 0.5
#     """
#     if total == 0:
#         return 1.0
#     pct = index / total
#     if pct < 0.33:
#         return 1.0
#     if pct < 0.66:
#         return 0.75
#     return 0.5


# def _normalize_role_title(keyword: str) -> str:
#     """
#     Convert a search keyword into a clean title-case role name.
#     e.g. 'python developer' → 'Python Developer'
#     """
#     return " ".join(w.capitalize() for w in keyword.strip().split())


# def _upsert_role_skills(role: Role, skills: list[Skill]) -> None:
#     """
#     For each skill extracted from jobs under this role keyword,
#     upsert a RoleSkill row. If the skill is new to the role, add it.
#     If it already exists, update importance_weight upward (more jobs
#     mentioning a skill → it's more important for that role).
#     """
#     total = len(skills)
#     for idx, skill in enumerate(skills):
#         weight = _importance_weight(idx, total)
#         rs, created = RoleSkill.objects.get_or_create(
#             role=role,
#             skill=skill,
#             defaults={"importance_weight": weight},
#         )
#         if not created and rs.importance_weight < weight:
#             # Raise importance if this job signals the skill is more critical
#             rs.importance_weight = weight
#             rs.save(update_fields=["importance_weight"])


# # ── public API ────────────────────────────────────────────────────────────────

# def purge_old_jobs(days: int = 30) -> int:
#     """
#     Delete jobs older than `days` days.
#     Keeps the DB lean so the jobs page always shows fresh listings.
#     Returns number of jobs deleted.
#     """
#     cutoff = timezone.now() - timedelta(days=days)
#     count, _ = Job.objects.filter(created_at__lt=cutoff).delete()
#     return count


# def sync_jobs(
#     country: str = "in",
#     max_pages: int = 2,
#     what: str = "",
# ) -> int:
#     """
#     Fetch jobs from Adzuna and:
#       - Save new Job rows
#       - Extract skills (spaCy only — no LLM)
#       - Write to skills_skill + jobs_jobskill
#       - Upsert roles_role + roles_roleskill using `what` as role title

#     Args:
#         country:   Adzuna country code — 'in', 'us', 'gb', 'ca', 'au'
#         max_pages: Pages to pull (each page = up to 50 jobs).
#         what:      Role keyword (e.g. 'python developer').
#                    Used as both the Adzuna search term and the Role title.

#     Returns:
#         Number of new jobs created.
#     """
#     seen: set = set()
#     created = 0

#     # Upsert the Role row for this keyword upfront (once per sync_jobs call)
#     role = None
#     if what:
#         role_title = _normalize_role_title(what)
#         role, _ = Role.objects.get_or_create(
#             title=role_title,
#             defaults={"description": f"Role extracted from live job listings for '{role_title}'."},
#         )

#     for page in range(1, max_pages + 1):
#         results = fetch_jobs(country=country, page=page, what=what)
#         if not results:
#             break

#         for r in results:
#             ext_id = r.get("id")
#             if not ext_id or str(ext_id) in seen:
#                 continue
#             seen.add(str(ext_id))

#             with transaction.atomic():
#                 job, created_flag = Job.objects.get_or_create(
#                     external_id=str(ext_id),
#                     defaults={
#                         "title":       r.get("title", "")[:512],
#                         "company":     r.get("company", {}).get("display_name", "")[:256],
#                         "location":    r.get("location", {}).get("display_name", "")[:256],
#                         "description": r.get("description", "")[:10_000],
#                         "url":         r.get("redirect_url", ""),
#                         "salary_min":  r.get("salary_min"),
#                         "salary_max":  r.get("salary_max"),
#                     },
#                 )

#                 if created_flag:
#                     created += 1
#                     text = f"{job.title} {job.description}"

#                     # Extract skills — spaCy only, no LLM
#                     skill_names = extract_skills(text, use_llm=False)[:20]

#                     # Save Skill + JobSkill rows
#                     skill_objects = []
#                     for name in skill_names:
#                         skill = _get_or_create_skill(name)
#                         JobSkill.objects.get_or_create(job=job, skill=skill)
#                         skill_objects.append(skill)

#                     # Upsert RoleSkill rows for this role keyword
#                     if role and skill_objects:
#                         _upsert_role_skills(role, skill_objects)

#     logger.info(
#         "sync_jobs done — country=%s, what=%r, new_jobs=%d, role=%s",
#         country, what, created, role.title if role else "none",
#     )
#     return created

"""
Job ingestion service: fetch from Adzuna, store in DB, extract skills,
and upsert Role + RoleSkill rows so the recommendation engine stays fresh.

Flow for every new job:
  1. Save Job row
  2. Extract skills via spaCy (no LLM — zero token cost)
  3. Save Skill + JobSkill rows
  4. Upsert Role row using the search keyword as the canonical role title
  5. Upsert RoleSkill rows — importance weight based on skill position in list
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.services.adzuna_service import fetch_jobs
from apps.skills.services import extract_skills, normalize_skill
from apps.jobs.models import Job, JobSkill
from apps.skills.models import Skill
from apps.roles.models import Role, RoleSkill

logger = logging.getLogger(__name__)


def _get_or_create_skill(name: str) -> Skill:
    nm = normalize_skill(name)
    skill, _ = Skill.objects.get_or_create(
        normalized_name=nm.lower(),
        defaults={"name": nm},
    )
    return skill


def _importance_weight(index: int, total: int) -> float:
    """Top third → 1.0, middle → 0.75, bottom → 0.5"""
    if total == 0:
        return 1.0
    pct = index / total
    if pct < 0.33:
        return 1.0
    if pct < 0.66:
        return 0.75
    return 0.5


def _normalize_role_title(keyword: str) -> str:
    return " ".join(w.capitalize() for w in keyword.strip().split())


def _upsert_role_skills(role: Role, skills: list) -> None:
    total = len(skills)
    for idx, skill in enumerate(skills):
        weight = _importance_weight(idx, total)
        rs, created = RoleSkill.objects.get_or_create(
            role=role,
            skill=skill,
            defaults={"importance_weight": weight},
        )
        if not created and rs.importance_weight < weight:
            rs.importance_weight = weight
            rs.save(update_fields=["importance_weight"])


def purge_old_jobs(days: int = 30) -> int:
    """Delete jobs older than `days` days. Returns count deleted."""
    cutoff = timezone.now() - timedelta(days=days)
    count, _ = Job.objects.filter(created_at__lt=cutoff).delete()
    return count


def sync_jobs(
    country: str = "in",
    max_pages: int = 2,
    what: str = "",
) -> int:
    """
    Fetch jobs from Adzuna and write to:
      jobs_job, skills_skill, jobs_jobskill, roles_role, roles_roleskill

    Returns number of new jobs created.
    """
    seen: set = set()
    created = 0

    role = None
    if what:
        role_title = _normalize_role_title(what)
        role, _ = Role.objects.get_or_create(
            title=role_title,
            defaults={"description": f"Role extracted from live job listings for '{role_title}'."},
        )

    for page in range(1, max_pages + 1):
        results = fetch_jobs(country=country, page=page, what=what)
        if not results:
            break

        for r in results:
            ext_id = r.get("id")
            if not ext_id or str(ext_id) in seen:
                continue
            seen.add(str(ext_id))

            with transaction.atomic():
                job, created_flag = Job.objects.get_or_create(
                    external_id=str(ext_id),
                    defaults={
                        "title":       r.get("title", "")[:512],
                        "company":     r.get("company", {}).get("display_name", "")[:256],
                        "location":    r.get("location", {}).get("display_name", "")[:256],
                        "description": r.get("description", "")[:10_000],
                        "url":         r.get("redirect_url", ""),
                        "salary_min":  r.get("salary_min"),
                        "salary_max":  r.get("salary_max"),
                    },
                )

                if created_flag:
                    created += 1
                    text = f"{job.title} {job.description}"
                    skill_names = extract_skills(text, use_llm=False)[:20]

                    skill_objects = []
                    for name in skill_names:
                        skill = _get_or_create_skill(name)
                        JobSkill.objects.get_or_create(job=job, skill=skill)
                        skill_objects.append(skill)

                    if role and skill_objects:
                        _upsert_role_skills(role, skill_objects)

    logger.info(
        "sync_jobs done — country=%s, what=%r, new_jobs=%d, role=%s",
        country, what, created, role.title if role else "none",
    )
    return created