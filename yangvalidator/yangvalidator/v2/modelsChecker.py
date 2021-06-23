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
        self.__all_modules_directory = all_modules_directory
        self.__working_directory = working_directory
        self.__existing_modules = existing_modules
        self.__dependencies = {}
        self.__missing = {}

    def check(self):
        for extracted_module in self.__existing_modules:
            parser = PyangParser([self.__all_modules_directory, self.__working_directory], extracted_module,
                                 self.__working_directory)
            self.__dependencies.update(parser.get_dependencies())

    def find_missing(self):
        """
        Find missing modules and save them as a key of a dictionary with list of possible revisions per module/key
        :return: dictionary of modules with its possible revisions
        """
        self.__missing = {}
        for key, val in self.__dependencies.items():
            if any(key == x.split('@')[0] for x in self.__existing_modules):
                continue
            else:
                self.__missing[key] = []
                for path in val:
                    # Get revision only
                    self.__missing[key].append(path.split('@')[-1].split('.')[0])

        return self.__missing

    def get_existing_dependencies(self):
        ret = {}
        found_repo_modules = False
        for key, val in self.__dependencies.items():
            for x in self.__existing_modules:
                if key == x.split('@')[0]:
                    ret[key] = {}
                    ret[key]['user-dependencies'] = x.split('@')[-1].split('.')[0]
                    ret[key]['repo-dependencies'] = []
                    for path in val:
                        # Get revision only
                        ret[key]['repo-dependencies'].append(path.split('@')[-1].split('.')[0])
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
        for module_name, revisions in self.__missing.items():
            revisions_to_sort = []
            for revision in revisions:
                year = int(revision.split('-')[0])
                month = int(revision.split('-')[1])
                day = int(revision.split('-')[2])
                try:
                    revisions_to_sort.append(datetime(year, month, day))
                except Exception as e:
                    if month == 2 and day == 29:
                        revisions_to_sort.append(datetime(year, month, 28))
                    else:
                        raise e
            
            ret.append('{}@{}.yang'.format(module_name, revisions[revisions_to_sort.index(max(revisions_to_sort))]))

        return ret
