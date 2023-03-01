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

import jinja2


class YangdumpProParser:
    """
    Cover the parsing of the module with yangdump-pro parser and validator
    """

    YANGDUMP_PRO_CMD = '/usr/bin/yangdump-pro'
    try:
        VERSION = check_output(f'{YANGDUMP_PRO_CMD} --version', shell=True).decode('utf-8').strip()
    except CalledProcessError:
        VERSION = 'undefined'
    LOG = logging.getLogger(__name__)

    def __init__(self, context_directories, file_name: str, working_directory: str):
        self.__working_directory = working_directory
        self.__yangdump_resfile = str(os.path.join(working_directory, file_name.replace('.yang', '.cres')))
        self.__yangdump_outfile = str(os.path.join(working_directory, file_name.replace('.yang', '.cout')))
        context = {'path': working_directory}
        path, filename = os.path.split(
            os.path.realpath(os.path.join(os.path.dirname(__file__), '../templates/yangdump-pro-yangvalidator.conf')),
        )
        rendered_config_text = (
            jinja2.Environment(loader=jinja2.FileSystemLoader(path)).get_template(filename).render(context)
        )
        yangdump_config_file = os.path.join(working_directory, 'yangdump-pro-yangvalidator.conf')
        with open(yangdump_config_file.format(working_directory), 'w') as ff:
            ff.write(rendered_config_text)

        cmds = [self.YANGDUMP_PRO_CMD, '--quiet-mode', '--config', yangdump_config_file]
        self.__yangdump_command = cmds + [os.path.join(working_directory, file_name)]

    def parse_module(self):
        yangdump_res: t.Dict[str, t.Union[str, int]] = {'time': datetime.now(timezone.utc).isoformat()}
        ypoutfp = open(self.__yangdump_outfile, 'w+')
        ypresfp = open(self.__yangdump_resfile, 'w+')

        status = call(self.__yangdump_command, stdout=ypoutfp, stderr=ypresfp)

        yangdump_output = yangdump_stderr = ''
        if os.path.isfile(self.__yangdump_outfile):
            ypoutfp.seek(0)
            for line in ypoutfp.readlines():
                yangdump_output += os.path.basename(line)
        else:
            pass
        yangdump_output = '' if yangdump_output == '\n' else yangdump_output

        ypresfp.seek(0)
        for line in ypresfp.readlines():
            yangdump_stderr += line
        ypoutfp.close()
        ypresfp.close()
        dirname = os.path.dirname(self.__working_directory)

        yangdump_res['stdout'] = yangdump_output.replace(f'{dirname}/', '')
        yangdump_res['stderr'] = yangdump_stderr.replace(f'{dirname}/', '')
        yangdump_res['name'] = 'yangdump-pro'
        yangdump_res['version'] = self.VERSION
        yangdump_res['code'] = status
        yangdump_res['command'] = ' '.join(self.__yangdump_command)
        return yangdump_res
