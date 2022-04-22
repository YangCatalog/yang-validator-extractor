# Copyright The IETF Trust 2021, All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = 'Miroslav Kovac'
__copyright__ = 'Copyright The IETF Trust 2021, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'miroslav.kovac@pantheon.tech'

import logging
import os
import typing as t
from datetime import datetime, timezone
from subprocess import CalledProcessError, call, check_output


class ConfdParser:
    """
    Cover the parsing of the module with confd parser and validator
    """
    CONFDC_CMD = '/home/yangvalidator/confd-{}/bin/confdc'.format(os.environ['CONFD_VERSION'])
    try:
        VERSION = check_output('{} --version'.format(CONFDC_CMD), shell=True).decode('utf-8').rstrip()
    except CalledProcessError:
        VERSION = 'undefined'
    LOG = logging.getLogger(__name__)

    def __init__(self, context_directories, file_name: str, working_directory: str):
        self.__working_directory = working_directory
        self.__confdc_resfile = os.path.join(working_directory, file_name.replace('.yang', '.cres'))
        self.__confdc_outfile = os.path.join(working_directory, file_name.replace('.yang', '.cout'))
        fxsfile = os.path.join(working_directory, file_name.replace('.yang', '.fxs'))
        self.__cmds = [self.CONFDC_CMD, '-o', fxsfile, '-W', 'all']
        self.__cmds.extend(['--yangpath', working_directory])
        for dep_dir in context_directories:
            if dep_dir not in self.__cmds:
                self.__cmds.extend(['--yangpath', dep_dir])
        self.__confdc_command = self.__cmds + ['-c', os.path.join(working_directory, file_name)]

    def parse_module(self):
        confdc_res: t.Dict[str, t.Union[str, int]] = {'time': datetime.now(timezone.utc).isoformat()}
        outfp = open(self.__confdc_outfile, 'w+')
        cresfp = open(self.__confdc_resfile, 'w+')

        self.LOG.info('Starting to confd parse use command {}'.format(' '.join(self.__confdc_command)))
        status = call(self.__confdc_command, stdout=outfp, stderr=cresfp)

        confdc_output = confdc_stderr = ''
        if os.path.isfile(self.__confdc_outfile):
            outfp.seek(0)
            for line in outfp.readlines():
                confdc_output += os.path.basename(line)
        else:
            pass

        cresfp.seek(0)
        for line in cresfp.readlines():
            confdc_stderr += os.path.basename(line)
        outfp.close()
        dirname = os.path.dirname(self.__working_directory)

        confdc_res['stdout'] = confdc_output.replace('{}/'.format(dirname), '')
        confdc_res['stderr'] = confdc_stderr.replace('{}/'.format(dirname), '')
        confdc_res['name'] = 'confdc'
        confdc_res['version'] = self.VERSION
        confdc_res['code'] = status
        confdc_res['command'] = ' '.join(self.__confdc_command)

        return confdc_res
