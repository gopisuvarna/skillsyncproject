# """Z
# APScheduler: sync fresh jobs on startup and every 6 hours,
# then automatically rebuild the FAISS index so recommendations
# stay current — no manual commands needed after deployment.

# Rate limiting strategy:
#   - adzuna_service.py adds a 1.5s delay between every API call
#   - On startup, only 1 page per keyword (not 2) to reduce burst volume
#   - Full 2-page sync runs every 6 hours when the server is idle
# """
# import logging
# from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.triggers.interval import IntervalTrigger

# logger = logging.getLogger(__name__)
# _scheduler = None

# _ROLE_KEYWORDS = [
#     "software engineer",
#     "python developer",
#     "frontend developer",
#     "backend developer",
#     "full stack developer",
#     "data scientist",
#     "machine learning engineer",
#     "devops engineer",
#     "data analyst",
#     "cloud engineer",
# ]


# def rebuild_faiss_index() -> int:
#     """
#     Rebuild the DB-based FAISS role index from the current roles_role table.
#     Returns the number of roles indexed.
#     """
#     from django.db.models import Prefetch
#     from apps.roles.models import Role, RoleSkill
#     from apps.embeddings.models import RoleEmbedding
#     from core.services.embedding_service import encode
#     from apps.roles.services import FAISSRoleIndex

#     roles = list(
#         Role.objects.prefetch_related(
#             Prefetch("skills", queryset=RoleSkill.objects.select_related("skill"))
#         ).all()
#     )

#     if not roles:
#         logger.warning("rebuild_faiss_index: no roles in DB — skipping")
#         return 0

#     texts, role_ids = [], []
#     for r in roles:
#         skill_names = [rs.skill.name for rs in r.skills.all()]
#         texts.append(f"{r.title} {' '.join(skill_names)}")
#         role_ids.append(str(r.id))

#     vectors = encode(texts)

#     for role, vec in zip(roles, vectors):
#         RoleEmbedding.objects.update_or_create(
#             role=role, defaults={"vector": vec}
#         )

#     index = FAISSRoleIndex()
#     index.build(vectors, role_ids)
#     logger.info("FAISS index rebuilt — %d roles indexed", len(roles))
#     return len(roles)


# def run_job_sync(startup: bool = False):
#     """
#     1. Purge jobs older than 30 days
#     2. Sync fresh jobs from Adzuna
#        → writes jobs_job, skills_skill, jobs_jobskill, roles_role, roles_roleskill
#     3. Rebuild FAISS index (isolated try/except — sync never fails because of FAISS)

#     startup=True  → 1 page per keyword (light touch, avoids burst 429)
#     startup=False → 2 pages per keyword (full sync every 6 hours)
#     """
#     pages = 1 if startup else 2
#     try:
#         from apps.jobs.services import sync_jobs, purge_old_jobs

#         # Step 1 — purge stale jobs
#         removed = purge_old_jobs(days=30)
#         if removed:
#             logger.info("Purged %d stale jobs (>30 days old)", removed)

#         # Step 2 — sync (1.5s delay per request built into adzuna_service)
#         total_created = 0
#         for keyword in _ROLE_KEYWORDS:
#             created = sync_jobs(country="in", what=keyword, max_pages=pages)
#             total_created += created

#         for keyword in _ROLE_KEYWORDS[:5]:
#             created = sync_jobs(country="us", what=keyword, max_pages=1)
#             total_created += created

#         logger.info("Job sync complete — %d new jobs added", total_created)

#         # Step 3 — rebuild FAISS (isolated so a failure here never loses jobs)
#         try:
#             indexed = rebuild_faiss_index()
#             logger.info("Recommendations updated — %d roles in index", indexed)
#         except Exception as faiss_err:
#             logger.warning(
#                 "FAISS rebuild failed (jobs were still saved): %s", faiss_err
#             )

#     except Exception as e:
#         logger.exception("Job sync failed: %s", e)


# def start_scheduler():
#     global _scheduler
#     if _scheduler is not None:
#         return

#     _scheduler = BackgroundScheduler()

#     # Startup sync — light (1 page per keyword) to avoid burst 429
#     _scheduler.add_job(
#         run_job_sync,
#         id="job_sync_startup",
#         trigger="date", 
#         kwargs={"startup": True},
#     )

#     # Full sync every 6 hours
#     _scheduler.add_job(
#         run_job_sync,
#         id="job_sync_interval",
#         trigger=IntervalTrigger(hours=6),
#         kwargs={"startup": False},
#     )

#     _scheduler.start()
#     logger.info(
#         "Scheduler started — light sync on startup, full sync every 6 hours"
#     )


# def stop_scheduler():
#     global _scheduler
#     if _scheduler:
#         _scheduler.shutdown()
#         _scheduler = None

"""
APScheduler: sync fresh jobs on startup and every 6 hours,
then automatically rebuild the FAISS index so recommendations
stay current — no manual commands needed after deployment.
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)
_scheduler = None

# _ROLE_KEYWORDS = [
#     "software engineer",
#     "python developer",
#     "frontend developer",
#     "backend developer",
#     "full stack developer",
#     "data scientist",
#     "machine learning engineer",
#     "devops engineer",
#     "data analyst",
#     "cloud engineer",
# ]
_ROLE_KEYWORDS = [
    # Software Engineering
    "software engineer",
    "software developer",
    "python developer",
    "java developer",
    "javascript developer",
    "nodejs developer",
    "react developer",
    "angular developer",
    "vue developer",
    "full stack developer",
    "frontend developer",
    "backend developer",
 
    # Mobile
    "mobile developer",
    "android developer",
    "ios developer",
    "flutter developer",
    "react native developer",
 
    # Data & AI
    "data scientist",
    "data analyst",
    "data engineer",
    "machine learning engineer",
    "ai engineer",
    "nlp engineer",
    "computer vision engineer",
    "deep learning engineer",
    "business intelligence analyst",
    "data architect",
 
    # Cloud & DevOps
    "devops engineer",
    "cloud engineer",
    "aws engineer",
    "azure engineer",
    "site reliability engineer",
    "platform engineer",
    "infrastructure engineer",
    "kubernetes engineer",
 
    # Security
    "cybersecurity engineer",
    "security analyst",
    "penetration tester",
 
    # Database
    "database administrator",
    "sql developer",
 
    # QA & Testing
    "qa engineer",
    "test automation engineer",
 
    # Architecture & Leadership
    "solutions architect",
    "software architect",
    "technical lead",
    "engineering manager",
    "product manager",
    "scrum master",
 
    # Emerging
    "blockchain developer",
    "web3 developer",
    "embedded systems engineer",
    "game developer",
]

def rebuild_faiss_index() -> int:
    from django.db.models import Prefetch
    from apps.roles.models import Role, RoleSkill
    from apps.embeddings.models import RoleEmbedding
    from core.services.embedding_service import encode
    from apps.roles.services import FAISSRoleIndex

    roles = list(
        Role.objects.prefetch_related(
            Prefetch("skills", queryset=RoleSkill.objects.select_related("skill"))
        ).all()
    )

    if not roles:
        print("[Scheduler] No roles in DB — skipping FAISS rebuild")
        return 0

    texts, role_ids = [], []
    for r in roles:
        skill_names = [rs.skill.name for rs in r.skills.all()]
        texts.append(f"{r.title} {' '.join(skill_names)}")
        role_ids.append(str(r.id))

    vectors = encode(texts)

    for role, vec in zip(roles, vectors):
        RoleEmbedding.objects.update_or_create(
            role=role, defaults={"vector": vec}
        )

    index = FAISSRoleIndex()
    index.build(vectors, role_ids)
    print(f"[Scheduler] FAISS index rebuilt — {len(roles)} roles indexed")
    return len(roles)


def run_job_sync(startup: bool = False):
    pages = 1 if startup else 3
    mode = "startup (light)" if startup else "full (6h interval)"
    print(f"[Scheduler] Job sync started — mode={mode}, pages_per_keyword={pages}")

    try:
        from apps.jobs.services import sync_jobs, purge_old_jobs

        # Step 1 — purge old jobs
        removed = purge_old_jobs(days=30)
        if removed:
            print(f"[Scheduler] Purged {removed} stale jobs (>30 days)")

        # Step 2 — sync India
        total_created = 0
        for keyword in _ROLE_KEYWORDS:
            created = sync_jobs(country="in", what=keyword, max_pages=pages)
            total_created += created
            print(f"[Scheduler] IN '{keyword}' → {created} new jobs")

        # Step 3 — sync US (top 5 only)
        us_pages = 1 if startup else 2
        for keyword in _ROLE_KEYWORDS[:5]:
            created = sync_jobs(country="us", what=keyword, max_pages=us_pages)
            total_created += created
            print(f"[Scheduler] US '{keyword}' → {created} new jobs")

        print(f"[Scheduler] Sync complete — {total_created} new jobs added total")

        # Step 4 — rebuild FAISS (isolated)
        try:
            indexed = rebuild_faiss_index()
            print(f"[Scheduler] Recommendations updated — {indexed} roles in index")
        except Exception as faiss_err:
            print(f"[Scheduler] FAISS rebuild failed (jobs were saved): {faiss_err}")

    except Exception as e:
        print(f"[Scheduler] Sync failed: {e}")
        logger.exception("Job sync failed: %s", e)


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        print("[Scheduler] Already running — skipping duplicate start")
        return

    _scheduler = BackgroundScheduler()

    # Immediate startup sync (light)
    _scheduler.add_job(
        run_job_sync,
        id="job_sync_startup",
        trigger="date",
        kwargs={"startup": True},
    )

    # Full sync every 6 hours
    _scheduler.add_job(
        run_job_sync,
        id="job_sync_interval",
        trigger=IntervalTrigger(hours=6),
        kwargs={"startup": False},
    )

    _scheduler.start()
    print("[Scheduler] APScheduler running — startup sync queued, full sync every 6h")


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None
        print("[Scheduler] Stopped")