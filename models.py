# (c) 2010 by Anton Korenyushkin

from django.db import connection
from django.db.models.signals import post_syncdb

from utils import read_file
from paths import INIT_SQL_PATH


def _run_init_sql(**kwargs):
    connection.cursor().execute(read_file(INIT_SQL_PATH))
    post_syncdb.disconnect(_run_init_sql)


post_syncdb.connect(_run_init_sql)
