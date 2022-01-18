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

import glob
import io
import logging
import os
from datetime import datetime, timezone

import pyang
from pyang import error, plugin
from pyang.plugins.depend import emit_depend
from yangvalidator.create_config import create_config
from yangvalidator.yangParser import create_context, restore_statements


class PyangParser:
    """
    Cover the parsing of the module with pyang parser and validator
    """
    VERSION = pyang.__version__
    LOG = logging.getLogger(__name__)

    def __init__(self, context_directories: list, file_name: str, working_directory: str):
        # Plugins array must be emptied before plugin init
        plugin.plugins = []
        plugin.init([])
        self.__ctx = create_context(':'.join(context_directories))
        self.__ctx.opts.lint_namespace_prefixes = []
        self.__ctx.opts.lint_modulename_prefixes = []
        self.__pyang_command = ['pyang']
        self.__infile = os.path.join(working_directory, file_name)
        self.__working_directory = working_directory
        self.__file_name = file_name

    def parse_module(self):
        if self.__file_name.startswith('ietf', 0):
            self.__ctx.opts.ietf = True
            self.__pyang_command.extend(['-p', self.__working_directory, '--ietf', self.__infile])
        elif self.__file_name.startswith('mef', 0):
            self.__ctx.opts.mef = True
            self.__pyang_command.extend(['-p', self.__working_directory, '--mef', self.__infile])
        elif self.__file_name.startswith('ieee', 0):
            self.__ctx.opts.ieee = True
            self.__pyang_command.extend(['-p', self.__working_directory, '--ieee', self.__infile])
        elif self.__file_name.startswith('bbf', 0):
            self.__ctx.opts.bbf = True
            self.__pyang_command.extend(['-p', self.__working_directory, '--bbf', self.__infile])
        else:
            self.__pyang_command.extend([self.__infile])
        for p in plugin.plugins:
            p.setup_ctx(self.__ctx)
        pyang_res = {'time': datetime.now(timezone.utc).isoformat()}
        self.LOG.info(' '.join(self.__pyang_command))
        with open(self.__infile, 'r', encoding='utf-8') as yang_file:
            module = yang_file.read()
            if module is None:
                self.LOG.info('no module provided')
            self.__ctx.add_module(self.__infile, module)

        self.__ctx.validate()
        pyang_stderr, pyang_output = self.__print_pyang_output()

        pyang_res['stdout'] = pyang_output
        pyang_res['stderr'] = pyang_stderr
        pyang_res['name'] = 'pyang'
        pyang_res['version'] = self.VERSION
        pyang_res['code'] = 0 if not pyang_stderr else 1
        pyang_res['command'] = ' '.join(self.__pyang_command)
        restore_statements()
        del self.__ctx
        return pyang_res

    def get_dependencies(self):
        self.__ctx.opts.depend_recurse = True
        self.__ctx.opts.depend_ignore = []
        for p in plugin.plugins:
            p.setup_ctx(self.__ctx)
        with open(self.__infile, 'r', encoding='utf-8') as yang_file:
            module = yang_file.read()
            if module is None:
                self.LOG.info('no module provided')
            m = self.__ctx.add_module(self.__infile, module)
            if m is None:
                m = []
            else:
                m = [m]
        self.__ctx.validate()

        config = create_config()
        yang_models = config.get('Directory-Section', 'save-file-dir')
        try:
            f = io.StringIO()
            emit_depend(self.__ctx, m, f)
            out = f.getvalue()
        except Exception as e:
            out = ''

        if len(out.split(':')) == 2 and out.split(':')[1].strip() != '':
            dependencies = out.split(':')[1].strip().split(' ')
        else:
            dependencies = []
        ret = {}
        for dep in dependencies:
            ret[dep] = glob.glob(r'{}/{}@*.yang'.format(yang_models, dep))
        restore_statements()
        del self.__ctx
        return ret

    def __print_pyang_output(self):
        err = ''
        out = ''
        for (epos, etag, eargs) in self.__ctx.errors:
            elevel = error.err_level(etag)
            if error.is_warning(elevel):
                kind = 'warning'
            else:
                kind = 'error'

            err += '{}: {}: {}\n'.format(epos, kind, error.err_to_str(etag, eargs))
        return err, out
