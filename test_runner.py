# (c) 2010 by Anton Korenyushkin

from subprocess import Popen, PIPE
from signal import SIGTERM
import shutil
import os

from django.test.simple import DjangoTestSuiteRunner

from utils import write_file
import settings
import paths


TEST_ROOT_PATH = '/tmp/chatlanian'
TEST_DRAFT_COUNT = 100


class TestRunner(DjangoTestSuiteRunner):
    def setup_test_environment(self, **kwargs):
        DjangoTestSuiteRunner.setup_test_environment(self, **kwargs)
        settings.ECILOP_PORT = paths.ECILOP_PORT = 9865
        paths.ROOT = paths.RootPath(TEST_ROOT_PATH)
        paths.create_paths(True)
        tablespace_paths = []
        for i in range(TEST_DRAFT_COUNT):
            draft_path = paths.ROOT.drafts[str(i)]
            os.makedirs(draft_path.tablespace)
            tablespace_paths.append(draft_path.tablespace)
            os.mkdir(draft_path.apps)
            os.mkdir(draft_path.libs)
            os.mkdir(draft_path.grantors)
            write_file(draft_path.config, '{}')
            write_file(draft_path.rsa_pub, 'public key')
        Popen(['sudo', 'chown', 'postgres'] + tablespace_paths).wait()
        os.symlink('0', paths.ROOT.drafts.curr)
        self._ecilop_process = Popen(
            [paths.ECILOP_EXE_PATH, '--config', paths.ROOT.etc.ecilop_conf],
            stdout=PIPE)
        self._ecilop_process.stdout.readline()
        self._ecilop_process.stdout.readline()

    def teardown_test_environment(self, **kwargs):
        DjangoTestSuiteRunner.teardown_test_environment(self, **kwargs)
        os.kill(self._ecilop_process.pid, SIGTERM)
        shutil.rmtree(TEST_ROOT_PATH)
