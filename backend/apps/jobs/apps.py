# import os
# import sys
# from django.apps import AppConfig


# class JobsConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'apps.jobs'
#     label = 'jobs'

#     def ready(self):
#         # Skip during management commands
#         skip = ['migrate', 'makemigrations', 'test', 'shell',
#                 'collectstatic', 'seed_roles', 'build_faiss']
#         if any(s in ' '.join(sys.argv) for s in skip):
#             return

#         # Django runserver runs two processes via StatReloader:
#         #   Parent (reloader): RUN_MAIN is NOT set → skip
#         #   Child  (server)  : RUN_MAIN = 'true'  → start
#         # Gunicorn: RUN_MAIN is never set, but ready() runs once → start
#         is_runserver = 'runserver' in ' '.join(sys.argv)
#         if is_runserver and os.environ.get('RUN_MAIN') != 'true':
#             return

#         try:
#             from apps.jobs.scheduler import start_scheduler
#             start_scheduler()
#             print("[Scheduler] APScheduler started — job sync running in background")
#         except Exception as e:
#             print(f"[Scheduler] Failed to start: {e}")


from django.apps import AppConfig


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.jobs'
    label = 'jobs'

    def ready(self):
        # No startup sync.
        # Skill-to-role matching runs on login via trigger_role_matching().
        pass