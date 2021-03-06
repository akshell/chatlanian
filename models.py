# (c) 2010-2011 by Anton Korenyushkin

from django.db import connection
from django.db.models.signals import post_syncdb

from utils import read_file
from paths import PATSAK_SQL_PATH, CHATLANIAN_SQL_PATH
import models


def _run_init_sql(**kwargs):
    connection.cursor().execute(
        (read_file(PATSAK_SQL_PATH) +
         read_file(CHATLANIAN_SQL_PATH)).replace('%', '%%'))
    post_syncdb.disconnect(_run_init_sql, sender=models)


post_syncdb.connect(_run_init_sql, sender=models)
