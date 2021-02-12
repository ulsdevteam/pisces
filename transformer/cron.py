from datetime import datetime

from django_cron import CronJobBase, Schedule

from .mappings import has_online_asset
from .models import DataObject


class CheckMissingOnlineAssets(CronJobBase):
    code = "transformer.online_assets"
    RUN_EVERY_MINS = 0
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)

    def do(self):
        print("Checking for recently added assets at {}".format(datetime.now()))
        for object in DataObject.objects.filter(object_type__in=["collection", "object"], online_pending=True).iterator():
            if has_online_asset(object.es_id):
                object.data["online"] = True
                object.indexed = False
                object.save()
                print("Online assets discovered for {}".format(object.es_id))
        print("Finished checking for recently added assets at {}\n".format(datetime.now()))
