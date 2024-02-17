from celery import Celery, Task
from celery.schedules import crontab, schedule
from datetime import timedelta

def celery_init_app(app) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.conf.beat_schedule = {
        "monthlyReport": {
            "task": "application.tasks.monthlyReport",
            # "schedule": crontab(hour=8, minute=00, day_of_month=1),
            # At 08:00 AM on day-of-month 1.
            "schedule": timedelta(seconds=20),
        },
        "remainder_emails": {
            "task": "application.tasks.remainder_emails",
            # "schedule": crontab(hour=19, minute=00),
            # “At 7:00 PM everyday
            "schedule": timedelta(seconds=20),
        },
        "reminder_google_chat": {
            "task": "application.tasks.reminder_google_chat",
            # "schedule": crontab(hour=20, minute=00),
            # At 8:00 PM everyday
            "schedule": timedelta(seconds=10),
        }
    }
    return celery_app


