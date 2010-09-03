# (c) 2010 by Anton Korenyushkin

from subprocess import Popen, PIPE
from signal import SIGTERM
import shutil
import os

from django.test.simple import DjangoTestSuiteRunner

from utils import write_file
from settings import DATABASES
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
            os.mkdir(draft_path.grantors)
            write_file(draft_path.config, '{}')
            write_file(draft_path.rsa_pub, 'public key')
        Popen(['sudo', 'chown', 'postgres'] + tablespace_paths).wait()
        os.symlink('0', paths.DRAFTS_PATH.curr)
        patsak_config_path = TEST_ROOT_PATH + '/patsak.conf'
        write_file(patsak_config_path, '''\
lib=%s/../patsak/lib
db=dbname=%s
''' % (paths.CHATLANIAN_PATH, DATABASES['default']['TEST_NAME']))
        self._ecilop_process = Popen(
            [
                paths.CHATLANIAN_PATH + '/../ecilop/ecilop',
                '--socket', paths.ECILOP_SOCKET_PATH,
                '--data', TEST_ROOT_PATH + '/data',
                '--locks', paths.LOCKS_PATH,
                '--patsak',
                paths.CHATLANIAN_PATH + '/../patsak/exe/common/patsak',
                '--patsak-config', patsak_config_path,
            ],
            stdout=PIPE)
        self._ecilop_process.stdout.readline()
        self._ecilop_process.stdout.readline()

    def teardown_test_environment(self, **kwargs):
        DjangoTestSuiteRunner.teardown_test_environment(self, **kwargs)
        os.kill(self._ecilop_process.pid, SIGTERM)
        shutil.rmtree(TEST_ROOT_PATH)
