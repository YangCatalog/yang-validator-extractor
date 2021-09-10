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

__author__ = "Miroslav Kovac"
__copyright__ = "Copyright The IETF Trust 2021, All Rights Reserved"
__license__ = "Apache License, Version 2.0"
__email__ = "miroslav.kovac@pantheon.tech"

from datetime import datetime

from yangvalidator.v2.pyangParser import PyangParser


class ModelsChecker:
    """
    Checks dependencies of the modules and it is able to find missing modules or
    different revision of the same module
    """

    def __init__(self, all_modules_directory: str, working_directory: str, existing_modules: list):
        self._all_modules_directory = all_modules_directory
        self._working_directory = working_directory
        self._existing_modules = existing_modules
        self._dependencies = {}
        self._missing = {}

    def check(self):
        for extracted_module in self._existing_modules:
            parser = PyangParser([self._all_modules_directory, self._working_directory], extracted_module,
                                 self._working_directory)
            self._dependencies.update(parser.get_dependencies())

    def find_missing(self):
        """
        Find missing modules and save them as a key of a dictionary with list of possible revisions per module/key
        :return: dictionary of modules with its possible revisions
        """
        self._missing = {}
        for name, paths in self._dependencies.items():
            if any(name == existing_module.split('@')[0] for existing_module in self._existing_modules):
                continue
            else:
                self._missing[name] = []
                for path in paths:
                    # Get revision only
                    self._missing[name].append(self.revision(path))

        return self._missing

    def get_existing_dependencies(self):
        ret = {}
        found_repo_modules = False
        for name, paths in self._dependencies.items():
            for existing_module in self._existing_modules:
                if name == existing_module.split('@')[0]:
                    ret[name] = {}
                    ret[name]['user-dependencies'] = self.revision(existing_module)
                    ret[name]['repo-dependencies'] = []
                    for path in paths:
                        # Get revision only
                        ret[name]['repo-dependencies'].append(self.revision(path))
                        found_repo_modules = True
        return ret, found_repo_modules

    def get_latest_revision(self):
        """
        Sort each missing dependency revision list and search for latest one. Also if there is revision date of
        29th of february, replace it for 28th.
        :return: list of modules with its latest revision
        """
        ret = []
        # Basic date extraction can fail if there are alphanumeric characters in the revision filename part
        for module_name, revisions in self._missing.items():
            revisions_to_sort = []
            for revision in revisions:
                year = int(revision.split('-')[0])
                month = int(revision.split('-')[1])
                day = int(revision.split('-')[2])
                try:
                    revisions_to_sort.append(datetime(year, month, day))
                except ValueError:
                    if month == 2 and day == 29:
                        revisions_to_sort.append(datetime(year, month, 28))
                    else:
                        raise

            ret.append('{}@{}.yang'.format(module_name, revisions[revisions_to_sort.index(max(revisions_to_sort))]))
        return ret

    def revision(self, path: str) -> str:
        return path.split('@')[-1].split('.')[0]
