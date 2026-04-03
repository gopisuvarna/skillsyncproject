# """
# APScheduler: sync fresh jobs on startup and every 6 hours,
# then automatically rebuild the FAISS index so recommendations
# stay current — no manual commands needed after deployment.
# """
# import logging
# from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.triggers.interval import IntervalTrigger

# logger = logging.getLogger(__name__)
# _scheduler = None

# # _ROLE_KEYWORDS = [
# #     "software engineer",
# #     "python developer",
# #     "frontend developer",
# #     "backend developer",
# #     "full stack developer",
# #     "data scientist",
# #     "machine learning engineer",
# #     "devops engineer",
# #     "data analyst",
# #     "cloud engineer",
# # ]
# _ROLE_KEYWORDS = [
#     # Software Engineering
#     "software engineer",
#     "software developer",
#     "python developer",
#     "java developer",
#     "javascript developer",
#     "nodejs developer",
#     "react developer",
#     "angular developer",
#     "vue developer",
#     "full stack developer",
#     "frontend developer",
#     "backend developer",
 
#     # Mobile
#     "mobile developer",
#     "android developer",
#     "ios developer",
#     "flutter developer",
#     "react native developer",
 
#     # Data & AI
#     "data scientist",
#     "data analyst",
#     "data engineer",
#     "machine learning engineer",
#     "ai engineer",
#     "nlp engineer",
#     "computer vision engineer",
#     "deep learning engineer",
#     "business intelligence analyst",
#     "data architect",
 
#     # Cloud & DevOps
#     "devops engineer",
#     "cloud engineer",
#     "aws engineer",
#     "azure engineer",
#     "site reliability engineer",
#     "platform engineer",
#     "infrastructure engineer",
#     "kubernetes engineer",
 
#     # Security
#     "cybersecurity engineer",
#     "security analyst",
#     "penetration tester",
 
#     # Database
#     "database administrator",
#     "sql developer",
 
#     # QA & Testing
#     "qa engineer",
#     "test automation engineer",
 
#     # Architecture & Leadership
#     "solutions architect",
#     "software architect",
#     "technical lead",
#     "engineering manager",
#     "product manager",
#     "scrum master",
 
#     # Emerging
#     "blockchain developer",
#     "web3 developer",
#     "embedded systems engineer",
#     "game developer",
# ]

# def rebuild_faiss_index() -> int:
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
#         print("[Scheduler] No roles in DB — skipping FAISS rebuild")
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
#     print(f"[Scheduler] FAISS index rebuilt — {len(roles)} roles indexed")
#     return len(roles)


# def run_job_sync(startup: bool = False):
#     pages = 1 if startup else 3
#     mode = "startup (light)" if startup else "full (6h interval)"
#     print(f"[Scheduler] Job sync started — mode={mode}, pages_per_keyword={pages}")

#     try:
#         from apps.jobs.services import sync_jobs, purge_old_jobs

#         # Step 1 — purge old jobs
#         removed = purge_old_jobs(days=30)
#         if removed:
#             print(f"[Scheduler] Purged {removed} stale jobs (>30 days)")

#         # Step 2 — sync India
#         total_created = 0
#         for keyword in _ROLE_KEYWORDS:
#             created = sync_jobs(country="in", what=keyword, max_pages=pages)
#             total_created += created
#             print(f"[Scheduler] IN '{keyword}' → {created} new jobs")

#         # Step 3 — sync US (top 5 only)
#         us_pages = 1 if startup else 2
#         for keyword in _ROLE_KEYWORDS[:5]:
#             created = sync_jobs(country="us", what=keyword, max_pages=us_pages)
#             total_created += created
#             print(f"[Scheduler] US '{keyword}' → {created} new jobs")

#         print(f"[Scheduler] Sync complete — {total_created} new jobs added total")

#         # Step 4 — rebuild FAISS (isolated)
#         try:
#             indexed = rebuild_faiss_index()
#             print(f"[Scheduler] Recommendations updated — {indexed} roles in index")
#         except Exception as faiss_err:
#             print(f"[Scheduler] FAISS rebuild failed (jobs were saved): {faiss_err}")

#     except Exception as e:
#         print(f"[Scheduler] Sync failed: {e}")
#         logger.exception("Job sync failed: %s", e)


# def start_scheduler():
#     global _scheduler
#     if _scheduler is not None:
#         print("[Scheduler] Already running — skipping duplicate start")
#         return

#     _scheduler = BackgroundScheduler()

#     # Immediate startup sync (light)
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
#     print("[Scheduler] APScheduler running — startup sync queued, full sync every 6h")


# def stop_scheduler():
#     global _scheduler
#     if _scheduler:
#         _scheduler.shutdown()
#         _scheduler = None
#         print("[Scheduler] Stopped")

"""
Skill-to-role matching triggered on user login.

What this does:
  1. User logs in
  2. A background thread fires immediately (login response is NOT delayed)
  3. Thread runs: user skills → FAISS search → re-rank → top 5 roles
  4. Result is cached in the DB (UserRoleCache table)
  5. Dashboard reads from cache instantly — no FAISS on every page load

No APScheduler. No startup sync. No job syncing here.
"""
import logging
import threading

logger = logging.getLogger(__name__)


def _compute_roles_for_user(user_id: int) -> None:
    """
    Runs in a background thread after login.
    Computes skill-to-role matches and caches the result.
    """
    try:
        from django.db.models import Prefetch
        from apps.skills.models import UserSkill
        from apps.roles.models import Role, RoleSkill
        from core.services.embedding_service import encode_single
        from apps.roles.services import get_faiss_index, re_rank, compute_skill_gap
        from apps.jobs.models import UserRoleCache
        import json

        # ── Step 1: get user skills ───────────────────────────────
        user_skills = list(
            UserSkill.objects.filter(user_id=user_id)
            .select_related('skill')
            .values('skill_id', 'skill__name')
        )

        if not user_skills:
            logger.info("Role cache: user %s has no skills — skipping", user_id)
            return

        user_skill_ids   = {str(s['skill_id']) for s in user_skills}
        user_skill_names = [s['skill__name'] for s in user_skills]
        user_text        = ' '.join(user_skill_names)

        # ── Step 2: FAISS search — user vector → top 30 candidates ─
        user_vec     = encode_single(user_text)
        faiss_index  = get_faiss_index()
        candidates   = faiss_index.search(user_vec, k=30)

        if not candidates:
            logger.info("Role cache: FAISS returned no candidates for user %s", user_id)
            return

        # ── Step 3: fetch role details for candidates ─────────────
        role_ids = [rid for rid, _ in candidates]
        roles = Role.objects.filter(id__in=role_ids).prefetch_related(
            Prefetch('skills', queryset=RoleSkill.objects.select_related('skill'))
        )
        role_map = {str(r.id): r for r in roles}

        candidate_roles = [
            {'id': str(rid), 'title': role_map[rid].title, 'description': role_map[rid].description}
            for rid in role_ids if rid in role_map
        ]

        role_skills_map = {
            str(r.id): [
                {
                    'skill_id':          str(rs.skill_id),
                    'skill_name':        rs.skill.name,
                    'importance_weight': rs.importance_weight,
                }
                for rs in r.skills.all()
            ]
            for r in roles
        }

        # ── Step 4: re-rank → top 5 ───────────────────────────────
        ranked = re_rank(
            candidate_roles,
            user_skill_ids,
            user_skill_names,
            role_skills_map,
            top_k=5,
        )

        # ── Step 5: attach skill gap to each role ─────────────────
        for role in ranked:
            rs_list = role_skills_map.get(str(role['id']), [])
            gap     = compute_skill_gap(user_skill_ids, rs_list)
            role['skill_gap'] = gap

        # ── Step 6: save to cache ─────────────────────────────────
        UserRoleCache.objects.update_or_create(
            user_id=user_id,
            defaults={'roles': json.dumps(ranked)},
        )

        logger.info(
            "Role cache: computed %d roles for user %s (%s)",
            len(ranked), user_id, [r['title'] for r in ranked]
        )

    except Exception as e:
        logger.exception("Role cache computation failed for user %s: %s", user_id, e)


def trigger_role_matching(user_id: int) -> None:
    """
    Called from the login view after successful authentication.
    Spawns a daemon thread — login response returns immediately.
    """
    t = threading.Thread(
        target=_compute_roles_for_user,
        args=(user_id,),
        daemon=True,
        name=f"role-match-user-{user_id}",
    )
    t.start()
    logger.info("Role matching thread started for user %s", user_id)