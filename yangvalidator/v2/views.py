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

import json
import logging
import os
import random
import shutil
import string
import sys
from zipfile import ZipFile

from django.core.handlers.wsgi import WSGIRequest
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from yangvalidator.create_config import create_config
from yangvalidator.v2.confdParser import ConfdParser
from yangvalidator.v2.illegalMethodError import IllegalMethodError
from yangvalidator.v2.modelsChecker import ModelsChecker
from yangvalidator.v2.pyangParser import PyangParser
from yangvalidator.v2.xymParser import XymParser
from yangvalidator.v2.yangdumpProParser import YangdumpProParser
from yangvalidator.v2.yanglintParser import YanglintParser

logger = logging.getLogger(__name__)


def validate(request: WSGIRequest, xym_result=None, json_body=None):
    """
    Validate yang module using 4 different validators. Yanglint, Pyang, Confdc, Yumadump-pro.
    Check if the are valid modules according to these validators and if not return problems that
    occurred while validating by each parser.
    :param json_body: json body sent from other function
    :param request: request sent from user
    :return: HTTP response with validated yang modules
    """
    try:
        if json_body is None:
            json_body = try_validate_and_load_data(request)
    except ValueError as e:
        # Missing json content or bad json content
        response_content = json.dumps({'Error': 'Not a json content - {}'.format(e)}, cls=DjangoJSONEncoder)
        return HttpResponse(response_content, status=400, content_type='application/json')
    except IllegalMethodError as e:
        # Method other then POST
        response_content = json.dumps({'Error': '{}'.format(e)}, cls=DjangoJSONEncoder)
        return HttpResponse(response_content, status=405, content_type='application/json')
    to_validate = json_body.get('modules-to-validate')
    if to_validate is None:
        # Missing modules to validate
        response_content = json.dumps({'Error': 'No module received for validation'}, cls=DjangoJSONEncoder)
        return HttpResponse(response_content, status=400, content_type='application/json')
    user_to_validate = to_validate.get('user-modules', [])
    repo_to_validate = to_validate.get('repo-modules', [])
    if len(user_to_validate) == 0 and len(repo_to_validate) == 0:
        # Missing modules to validate
        response_content = json.dumps({'Error': 'No module received for validation'}, cls=DjangoJSONEncoder)
        return HttpResponse(response_content, status=400, content_type='application/json')

    config = load_config()
    tmp = config.get('Directory-Section', 'temp')
    yang_models = config.get('Directory-Section', 'save-file-dir')
    suffix = create_random_suffx()
    work_dir = '{}/yangvalidator/yangvalidator-v2-workdir-{}'.format(tmp, suffix)
    results = {}
    if xym_result is not None:
        results['xym'] = xym_result
    try:
        os.mkdir(work_dir)
        modules_to_validate = []
        skipped_modules = []
        dependencies = json_body.get('dependencies', {})

        # Keep this uncommented code in here. Several lines bellow explaind why we want to keep this
        # user_dependencies = dependencies.get('user-modules', [])

        repo_dependencies = dependencies.get('repo-modules', [])

        # Copy modules that you need to validate to working directory
        for module_to_validate in repo_to_validate:
            # skip modules that are in dependencies
            skip = False
            for repo_dependency in repo_dependencies:
                if repo_dependency.split('@')[0] == module_to_validate.split('@')[0]:
                    skipped_modules.append(module_to_validate)
                    skip = True
                    break
            if skip:
                continue
            shutil.copy(os.path.join(yang_models, module_to_validate), work_dir)
            modules_to_validate.append(module_to_validate)

        for module_to_validate in user_to_validate:
            skip = False
            for repo_dependency in repo_dependencies:
                if repo_dependency.split('@')[0] == module_to_validate.split('@')[0]:
                    skipped_modules.append(module_to_validate)
                    skip = True
                    break
            if skip:
                continue
            shutil.copy(os.path.join(tmp, 'yangvalidator', json_body['cache'], module_to_validate), work_dir)
            modules_to_validate.append(module_to_validate)

        if len(skipped_modules) > 0:
            results['warning'] = 'Following modules {} were skipped from validation because you chose different repo' \
                                 ' modules as a dependency with same name'.format(', '.join(skipped_modules))

        # UI sends the users dependencies anyway for better code readability but it s not used anymore in here.
        # please keep following code for understanding why we are receiving user_dependencies.
        # These dependencies are already copied to working directory in step above when copying user modules to
        # validate.
        #
        # for dependency in user_dependencies:
        #     shutil.copy(os.path.join(tmp, json_body['cache'], dependency), work_dir)

        # Copy rest of dependencies to working directory
        for dependency in repo_dependencies:
            shutil.copy(os.path.join(yang_models, dependency), work_dir)
        # Validate each yang file with all parsers use only working directory for all dependencies
        for module_to_validate in modules_to_validate:
            # validate pyang
            pyang_parser = PyangParser([work_dir], module_to_validate, work_dir)
            results_pyang = pyang_parser.parse_module()
            # validate confd
            confd_parser = ConfdParser([work_dir], module_to_validate, work_dir)
            results_confd = confd_parser.parse_module()
            # validate yanglint
            yanglint_parser = YanglintParser([work_dir], module_to_validate, work_dir)
            results_yanglint = yanglint_parser.parse_module()
            # validate yangdump-pro
            yangdump_pro_parser = YangdumpProParser([work_dir], module_to_validate, work_dir)
            results_yangdump_pro = yangdump_pro_parser.parse_module()
            # merge results of one file
            results[module_to_validate] = {'pyang': results_pyang,
                                           'confd': results_confd,
                                           'yanglint': results_yanglint,
                                           'yangdump-pro': results_yangdump_pro
                                           }
    except Exception as e:
        results['error'] = 'Failed to parse a document - {}'.format(e)
        logger.error('Failed to parse module - {}'.format(e))
    finally:
        logger.info('Removing temporary directories')
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)

        cache_tmp_path = os.path.join(tmp, 'yangvalidator', json_body.get('cache', ''))
        if os.path.exists(cache_tmp_path):
            shutil.rmtree(cache_tmp_path)

    return HttpResponse(json.dumps({"output": results}, cls=DjangoJSONEncoder), content_type='application/json')


def validate_rfc(request):
    try_validate_and_load_data(request)
    payload_body = json.loads(request.body)
    rfc = payload_body.get('rfc')
    logger.info('validating rfc {}'.format(rfc))
    url = 'https://tools.ietf.org/rfc/rfc{!s}.txt'.format(rfc)
    config = load_config()
    tmp = config.get('Directory-Section', 'temp')
    suffix = create_random_suffx()
    working_dir = '{}/yangvalidator/yangvalidator-v2-cache-{}'.format(tmp, suffix)
    return extract_files(request, url, payload_body.get('latest', True), working_dir)


def validate_draft(request):
    try_validate_and_load_data(request)
    payload_body = json.loads(request.body)
    draft = payload_body.get('draft')
    if draft.endswith('.txt'):
        draft = draft[:-4]
    logger.info('validating draft {}'.format(draft))
    url = 'https://tools.ietf.org/id/{!s}.txt'.format(draft)
    config = load_config()
    tmp = config.get('Directory-Section', 'temp')
    suffix = create_random_suffx()
    working_dir = '{}/yangvalidator/yangvalidator-v2-cache-{}'.format(tmp, suffix)
    return extract_files(request, url, payload_body.get('latest', True), working_dir)


def upload_setup(request):
    try_validate_and_load_data(request)
    payload_body = json.loads(request.body)
    latest = payload_body.get('latest', False)
    get_from_options = payload_body.get('get-from-options', False)
    config = load_config()
    tmp = config.get('Directory-Section', 'temp')
    suffix = create_random_suffx()
    working_dir = '{}/yangvalidator/yangvalidator-v2-cache-{}'.format(tmp, suffix)
    os.mkdir(working_dir)
    with open('{}/pre-setup.json'.format(working_dir), 'w') as f:
        json.dump({'latest': latest,
                      'get-from-options': get_from_options
                      }, f)
    
    return HttpResponse(json.dumps({'output': {'cache': working_dir.split('/')[-1]}}), status=200, content_type='application/json')


def upload_draft(request):
    return upload_draft_id(request, None)


def upload_draft_id(request, id):
    config = load_config()
    tmp = config.get('Directory-Section', 'temp')
    working_dir = '{}/yangvalidator/{}'.format(tmp, id)
    if os.path.exists(working_dir):
        with open('{}/pre-setup.json'.format(working_dir), 'r') as f:
            setup = json.load(f)
    else:
        return HttpResponse(json.dumps({'Error': 'Cache file with id - {} does not exist.'
                                                 ' Please use pre setup first. Post request on path'
                                                 ' /yangvalidator/v2/upload-files-setup where you provide'
                                                 ' "latest" key with true or false variable'.format(id)},
                                       cls=DjangoJSONEncoder), status=400, content_type='application/json')

    latest = setup.get('latest', True)
    results = []
    working_dirs = []
    try:
        for file in request.FILES.getlist('data'):
            suffix = create_random_suffx()
            working_dir = '{}/yangvalidator/yangvalidator-v2-cache-{}'.format(tmp, suffix)
            os.mkdir(working_dir)
            working_dirs.append(working_dir)
            filepath = os.path.join(working_dir, file.name)
            with open(filepath, 'wb+') as f:
                for chunk in file.chunks():
                    f.write(chunk)
            output = json.loads(extract_files(request, filepath, latest, working_dir, remove_working_dir=False).content)
            output['document-name'] = file.name
            results.append(output)
    except Exception as e:
        for wd in working_dirs:
            if os.path.exists(wd):
                shutil.rmtree(wd)
        return HttpResponse(json.dumps({'Error': "Failed to upload and validate documents - {}".format(e)},
                                       cls=DjangoJSONEncoder),
                            status=400, content_type='application/json')
    return HttpResponse(json.dumps(results, cls=DjangoJSONEncoder), status=200, content_type='application/json')


def upload_file(request, id):
    saved_files = []
    config = load_config()
    tmp = config.get('Directory-Section', 'temp')
    working_dir = '{}/yangvalidator/{}'.format(tmp, id)
    yang_models = config.get('Directory-Section', 'save-file-dir')
    presetup_path = '{}/pre-setup.json'.format(working_dir)
    if os.path.exists(presetup_path):
        with open(presetup_path, 'r') as f:
            setup = json.load(f)
    else:
        return HttpResponse(json.dumps({'Error': 'Cache file with id - {} does not exist.'
                                                 ' Please use pre setup first. Post request on path'
                                                 ' /yangvalidator/v2/upload-files-setup where you provide'
                                                 ' "latest" and "get_from_options" key with true or false'
                                                 ' variable'.format(id)},
                                       cls=DjangoJSONEncoder), status=400, content_type='application/json')

    latest = setup.get('latest', False)
    get_from_options = setup.get('get-from-options', True)
    try:
        for file in request.FILES.getlist('data'):
            name, ext = os.path.splitext(file.name)

            if ext == '.yang':
                with open(os.path.join(working_dir, file.name), 'wb+') as f:
                    for chunk in file.chunks():
                        f.write(chunk)
                saved_files.append(file.name)

            if ext == '.zip':
                zipfilename = os.path.join(working_dir, file.name)
                with open(zipfilename, 'wb+') as f:
                    for chunk in file.chunks():
                        f.write(chunk)
                zf = ZipFile(zipfilename, "r")
                zf.extractall(working_dir)
                saved_files = [filename for filename in zf.namelist() if filename.endswith('.yang')]
    except Exception as e:
        logger.error('Error: %s : %s' % (working_dir, e))
        if os.path.exists(working_dir):
            shutil.rmtree(working_dir)
        return HttpResponse(json.dumps({'Error': "Failed to get yang files"}, cls=DjangoJSONEncoder),
                            status=400, content_type='application/json')
    return create_output(request, yang_models, None, latest, working_dir, saved_files,
                         choose_options=get_from_options)


def extract_files(request,  url: str, latest: bool, working_dir: str, remove_working_dir=True):
    config = load_config()
    yang_models = config.get('Directory-Section', 'save-file-dir')
    xym_parser = XymParser(url, working_dir)
    extracted_modules, xym_response = xym_parser.parse_and_extract()
    return create_output(request, yang_models, url, latest, working_dir, extracted_modules, xym_response,
                         remove_working_dir=remove_working_dir)


def create_output(request, yang_models: str, url, latest: bool, working_dir: str, extracted_modules: list = None,
                  xym_response: dict = None, choose_options=False, remove_working_dir=True):
    checker = ModelsChecker(yang_models, working_dir, extracted_modules)
    checker.check()
    missing = checker.find_missing()
    # if each missing has only one repo module use latest we are using that one anyway
    if check_missing_amount_one_only(missing):
        latest = True
    if len(extracted_modules) == 0:
        if xym_response is None:
            response_content = json.dumps({'Error': 'Failed to load any yang modules. Please provide at least one'
                                                    ' yang module. File must have .yang extension'},
                                          cls=DjangoJSONEncoder)
            return HttpResponse(response_content, status=400, content_type='application/json')
        elif len(xym_response.get('stderr')):
            response_content = json.dumps({'Error': 'Failed to xym parse url {}'.format(url),
                                           "xym": xym_response}, cls=DjangoJSONEncoder)
        else:
            response_content = json.dumps({'Error': 'No modules found using xym in url {}'.format(url),
                                           "xym": xym_response}, cls=DjangoJSONEncoder)
        if os.path.exists(working_dir) and remove_working_dir:
            shutil.rmtree(working_dir)
        return HttpResponse(response_content, status=200, content_type='application/json')
    elif choose_options:
        existing_dependencies, found_repo_modules = checker.get_existing_dependencies()
        json_body = {
            'modules-to-validate': {
                'user-modules': extracted_modules
            },
            'dependencies': {
                'missing': missing,
                'existing': existing_dependencies
            },
            'cache': working_dir.split('/')[-1]
        }
        if len(missing) == 0 and not found_repo_modules:
            http_response = validate(request, xym_response, json_body)
            if os.path.exists(working_dir) and remove_working_dir:
                shutil.rmtree(working_dir)
            return http_response
        return HttpResponse(json.dumps({'output': json_body}, cls=DjangoJSONEncoder),
                            status=202, content_type='application/json')
    elif latest:
        json_body = {
            'modules-to-validate': {
                'user-modules': extracted_modules
            },
            'dependencies': {
                'repo-modules': checker.get_latest_revision()
            },
            'cache': working_dir.split('/')[-1]
        }

        http_response = validate(request, xym_response, json_body)
        if os.path.exists(working_dir) and remove_working_dir:
            shutil.rmtree(working_dir)
        return http_response
    elif len(missing) == 0:
        json_body = {
            'modules-to-validate': {
                'user-modules': extracted_modules
            },
            'cache': working_dir.split('/')[-1]
        }
        http_response = validate(request, xym_response, json_body)
        return http_response
    else:
        if xym_response is not None:
            response =\
                {
                    'modules-to-validate': {
                        'user-modules': extracted_modules
                    },
                    'xym': xym_response,
                    'dependencies': {
                        'missing': missing,
                    },
                    'cache': working_dir.split('/')[-1]
                }
        else:
            response =\
                {
                    'modules-to-validate': {
                        'user-modules': extracted_modules
                    },
                    'dependencies': {
                        'missing': missing,
                    },
                        'cache': working_dir.split('/')[-1]
                }
        return HttpResponse(json.dumps({'output': response}, cls=DjangoJSONEncoder),
                            status=202, content_type='application/json')


def try_validate_and_load_data(request: WSGIRequest):
    """
    Check if request is POST and try to parse byte string to json format
    :param request: request sent from user
    :return: Parsed json string
    """
    if request.method != 'POST':
        raise IllegalMethodError(request.method)
    return json.loads(request.body)


def create_random_suffx():
    """
    Create random suffix to create new temp directory
    :return: suffix of random 8 letters
    """
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(8))


def load_config():
    """
    Load and parse yangcatalog config file
    :return: parsed config file
    """
    config = create_config()
    return config


def check_missing_amount_one_only(missing: dict):
    for val in missing.values():
        if len(val) > 1:
            return False
    return True


if not os.path.exists('{}/yangvalidator'.format(load_config().get('Directory-Section', 'temp'))):
    os.makedirs('{}/yangvalidator'.format(load_config().get('Directory-Section', 'temp')))