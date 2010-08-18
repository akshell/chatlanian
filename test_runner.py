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
            draft_path = paths.DRAFTS_PATH + '/' + str(i)
            tablespace_path = draft_path + '/tablespace'
            os.makedirs(tablespace_path)
            tablespace_paths.append(tablespace_path)
            os.mkdir(draft_path + '/apps')
            write_file(draft_path + '/config', '{}')
            write_file(draft_path + '/rsa.pub', 'public key')
        Popen(['sudo', 'chown', 'postgres'] + tablespace_paths).wait()
        os.symlink('0', paths.CURR_DRAFT_PATH)

    def teardown_test_environment(self, **kwargs):
        DjangoTestSuiteRunner.teardown_test_environment(self, **kwargs)
        shutil.rmtree(TEST_ROOT_PATH)
