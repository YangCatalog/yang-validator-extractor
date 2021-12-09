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
from datetime import datetime, timezone
from subprocess import CalledProcessError, call, check_output

import jinja2


class YangdumpProParser:
    """
    Cover the parsing of the module with yangdump-pro parser and validator
    """
    YANGDUMP_PRO_CMD = '/usr/bin/yangdump-pro'
    try:
        VERSION = check_output(YANGDUMP_PRO_CMD + ' --version', shell=True).decode('utf-8').strip()
    except CalledProcessError:
        VERSION = 'undefined'
    LOG = logging.getLogger(__name__)

    def __init__(self, context_directories, file_name: str, working_directory: str):
        self.__yangdump_resfile = str(os.path.join(working_directory, file_name.replace('.yang', '.cres')))
        self.__yangdump_outfile = str(os.path.join(working_directory, file_name.replace('.yang', '.cout')))
        context = {'path': working_directory}
        path, filename = os.path.split(
            os.path.dirname(__file__) + '/../templates/yangdump-pro-yangvalidator.conf')
        rendered_config_text = jinja2.Environment(loader=jinja2.FileSystemLoader(path or './')
                                                  ).get_template(filename).render(context)
        yangdump_config_file = '{}/yangdump-pro-yangvalidator.conf'.format(working_directory)
        with open(yangdump_config_file.format(working_directory), 'w') as ff:
            ff.write(rendered_config_text)

        cmds = [self.YANGDUMP_PRO_CMD, '--quiet-mode', '--config', yangdump_config_file]
        self.__yangdump_command = cmds + ['{}/{}'.format(working_directory, file_name)]

    def parse_module(self):
        yangdump_res = {}
        ypoutfp = open(self.__yangdump_outfile, 'w+')
        ypresfp = open(self.__yangdump_resfile, 'w+')

        status = call(self.__yangdump_command, stdout=ypoutfp, stderr=ypresfp)
        yangdump_res['time'] = datetime.now(timezone.utc).isoformat()

        yangdump_output = yangdump_stderr = ''
        if os.path.isfile(self.__yangdump_outfile):
            ypoutfp.seek(0)
            for line in ypoutfp.readlines():
                yangdump_output += os.path.basename(line)
        else:
            pass
        yangdump_res['stdout'] = '' if yangdump_output == '\n' else yangdump_output

        ypresfp.seek(0)

        for line in ypresfp.readlines():
            yangdump_stderr += line
        ypoutfp.close()
        ypresfp.close()
        yangdump_res['stderr'] = yangdump_stderr
        yangdump_res['name'] = 'yangdump-pro'
        yangdump_res['version'] = self.VERSION
        yangdump_res['code'] = status
        yangdump_res['command'] = ' '.join(self.__yangdump_command)
        return yangdump_res
