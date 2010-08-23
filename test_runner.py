# (c) 2010 by Anton Korenyushkin

from subprocess import Popen
import shutil
import os

from django.test.simple import DjangoTestSuiteRunner

from utils import write_file
import paths


TEST_ROOT_PATH = '/tmp/chatlanian'
TEST_DRAFT_COUNT = 100


class TestRunner(DjangoTestSuiteRunner):
    def setup_test_environment(self, **kwargs):
        DjangoTestSuiteRunner.setup_test_environment(self, **kwargs)
        paths.setup_paths(TEST_ROOT_PATH)
        paths.create_paths()
        tablespace_paths = []
        for i in range(TEST_DRAFT_COUNT):
            draft_path = paths.DRAFTS_PATH[str(i)]
            os.makedirs(draft_path.tablespace)
            tablespace_paths.append(draft_path.tablespace)
            os.mkdir(draft_path.apps)
            os.mkdir(draft_path.libs)
            write_file(draft_path.config, '{}')
            write_file(draft_path.rsa_pub, 'public key')
        Popen(['sudo', 'chown', 'postgres'] + tablespace_paths).wait()
        os.symlink('0', paths.DRAFTS_PATH.curr)

    def teardown_test_environment(self, **kwargs):
        DjangoTestSuiteRunner.teardown_test_environment(self, **kwargs)
        shutil.rmtree(TEST_ROOT_PATH)
