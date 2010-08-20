# (c) 2010 by Anton Korenyushkin

import os
import shutil
import httplib

from piston.handler import BaseHandler
from django.db import connection

from error import Error
from paths import TMP_PATH, DEVS_PATH


class AppHandler(BaseHandler):
    allowed_methods = ('DELETE')

    def delete(self, request, app_name):
        app_path = DEVS_PATH[request.dev_name].apps[app_name]
        if not os.path.exists(app_path):
            raise Error(
                'The app "%s" does not exist.' % app_name,
                status=httplib.NOT_FOUND)
        app_id = (request.dev_name + ':' + app_name).lower()
        tmp_app_path = TMP_PATH[app_id]
        os.rename(app_path, tmp_app_path)
        shutil.rmtree(tmp_app_path)
        connection.cursor().execute('SELECT ak.drop_schemas(%s)', (app_id,))
