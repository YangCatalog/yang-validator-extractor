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


class YanglintParser:
    """
    Cover the parsing of the module with yanglint parser and validator
    """

    YANGLINT_CMD = '/usr/local/bin/yanglint'
    try:
        VERSION = check_output(YANGLINT_CMD + ' --version', shell=True).decode('utf-8').rstrip()
    except CalledProcessError:
        VERSION = 'undefined'
    LOG = logging.getLogger(__name__)

    def __init__(self, context_directories, file_name: str, working_directory: str):
        self.__working_directory = working_directory
        self.__yanglint_resfile = str(os.path.join(working_directory, file_name) + '.lres')
        self.__yanglint_outfile = str(os.path.join(working_directory, file_name) + '.lout')
        cmds = [self.YANGLINT_CMD, '-i', '-p', working_directory]
        for dep_dir in context_directories:
            if dep_dir not in cmds:
                cmds.extend(['-p', dep_dir])
        self.__yanglint_cmd = cmds + [os.path.join(working_directory, file_name)]

    def parse_module(self):
        yanglint_res: t.Dict[str, t.Union[str, int]] = {'time': datetime.now(timezone.utc).isoformat()}

        yresfp = open(self.__yanglint_resfile, 'w+')
        outfp = open(self.__yanglint_outfile, 'w+')
        status = call(self.__yanglint_cmd, stdout=outfp, stderr=yresfp)
        self.LOG.info('Starting to yanglint parse use command {}'.format(' '.join(self.__yanglint_cmd)))
        yanglint_output = yanglint_stderr = ''
        if os.path.isfile(self.__yanglint_outfile):
            outfp.seek(0)
            for line in outfp.readlines():
                yanglint_output += os.path.basename(line)
        else:
            pass

        yresfp.seek(0)
        for line in yresfp.readlines():
            yanglint_stderr += line
        outfp.close()
        yresfp.close()
        dirname = os.path.dirname(self.__working_directory)

        yanglint_res['stdout'] = yanglint_output.replace('{}/'.format(dirname), '')
        yanglint_res['stderr'] = yanglint_stderr.replace('{}/'.format(dirname), '')
        yanglint_res['name'] = 'yanglint'
        yanglint_res['version'] = self.VERSION
        yanglint_res['code'] = status
        yanglint_res['command'] = ' '.join(self.__yanglint_cmd)

        return yanglint_res
