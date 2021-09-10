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

import fnmatch
import json
import logging
import os
import random
import shutil
import string
from zipfile import ZipFile

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
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
        return JsonResponse({'Error': 'Not a json content - {}'.format(e)}, status=400)
    except IllegalMethodError as e:
        # Method other then POST
        return JsonResponse({'Error': '{}'.format(e)}, status=405)
    to_validate = json_body.get('modules-to-validate')
    if to_validate is None:
        # Missing modules to validate
        return JsonResponse({'Error': 'No module received for validation'}, status=400)
    user_to_validate = to_validate.get('user-modules', [])
    repo_to_validate = to_validate.get('repo-modules', [])
    if len(user_to_validate) == 0 and len(repo_to_validate) == 0:
        # Missing modules to validate
        return JsonResponse({'Error': 'No module received for validation'}, status=400)

    config = create_config()
    tmp = config.get('Directory-Section', 'temp')
    yang_models = config.get('Directory-Section', 'save-file-dir')
    while True:
        suffix = create_random_suffix()
        work_dir = '{}/yangvalidator/yangvalidator-v2-workdir-{}'.format(tmp, suffix)
        if not os.path.exists(work_dir):
            break
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
        for group_to_validate, source in ((repo_to_validate, yang_models),
                                          (user_to_validate, os.path.join(tmp, 'yangvalidator', json_body['cache']))):

            for module_to_validate in group_to_validate:
                # skip modules that are in dependencies
                for repo_dependency in repo_dependencies:
                    if repo_dependency.split('@')[0] == module_to_validate.split('@')[0]:
                        skipped_modules.append(module_to_validate)
                        break
                else:
                    shutil.copy(os.path.join(source, module_to_validate), work_dir)
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
            results[module_to_validate] = {}
            for Parser, name in ((PyangParser, 'pyang'), (ConfdParser, 'confd'),
                                 (YanglintParser, 'yanglint'), (YangdumpProParser, 'yangdump-pro')):
                parser_results = Parser([work_dir], module_to_validate, work_dir).parse_module()
                results[module_to_validate][name] = parser_results
    except Exception as e:
        results['error'] = 'Failed to parse a document - {}'.format(e)
        logger.exception('Failed to parse module - {}'.format(e))
    finally:
        logger.info('Removing temporary directories')
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)

        cache_tmp_path = os.path.join(tmp, 'yangvalidator', json_body.get('cache', ''))
        if os.path.exists(cache_tmp_path):
            shutil.rmtree(cache_tmp_path)
    return JsonResponse({'output': results})


def validate_doc(request):
    doc_type = request.path.split('/')[-1]
    payload_body = try_validate_and_load_data(request)
    doc_name = payload_body.get(doc_type)
    if doc_name.endswith('.txt'):
        doc_name = doc_name[:-4]
    logger.info('validating {} {}'.format(doc_type, doc_name))
    config = create_config()
    tmp = config.get('Directory-Section', 'temp')
    ietf_dir = config.get('Directory-Section', 'ietf-directory')
    if doc_type == 'draft':
        draft_dir = os.path.join(ietf_dir, 'my-id-archive-mirror')
        matching_drafts = fnmatch.filter(os.listdir(draft_dir), '{}*.txt'.format(doc_name))
        if matching_drafts:
            draft_file = sorted(matching_drafts)[-1]
            url = os.path.join(draft_dir, draft_file)
        else:
            url = 'https://tools.ietf.org/id/{!s}.txt'.format(doc_name)
    elif doc_type == 'rfc':
        rfc_file = 'rfc{}.txt'.format(doc_name)
        path = os.path.join(ietf_dir, 'rfc', rfc_file)
        if os.path.exists(path):
            url = path
        else:
            url = 'https://tools.ietf.org/rfc/{}'.format(rfc_file)
    while True:
        suffix = create_random_suffix()
        working_dir = '{}/yangvalidator/yangvalidator-v2-cache-{}'.format(tmp, suffix)
        if not os.path.exists(working_dir):
            break
    return extract_files(request, url, payload_body.get('latest', True), working_dir)


def upload_setup(request):
    payload_body = try_validate_and_load_data(request)
    latest = payload_body.get('latest', False)
    get_from_options = payload_body.get('get-from-options', False)
    config = create_config()
    tmp = config.get('Directory-Section', 'temp')
    while True:
        suffix = create_random_suffix()
        working_dir = '{}/yangvalidator/yangvalidator-v2-cache-{}'.format(tmp, suffix)
        if not os.path.exists(working_dir):
            break
    os.mkdir(working_dir)
    with open('{}/pre-setup.json'.format(working_dir), 'w') as f:
        json.dump({'latest': latest,
                      'get-from-options': get_from_options
                      }, f)
    return JsonResponse({'output': {'cache': working_dir.split('/')[-1]}})


def upload_draft(request):
    return upload_draft_id(request, None)

def load_pre_setup(working_dir, id):
    presetup_path = '{}/pre-setup.json'.format(working_dir)
    if os.path.exists(presetup_path):
        with open(presetup_path, 'r') as f:
            return json.load(f)
    else:
        return JsonResponse({'Error': 'Cache file with id - {} does not exist.'
                                      ' Please use pre setup first. Post request on path'
                                      ' /yangvalidator/v2/upload-files-setup where you provide'
                                      ' "latest" and "get-from-options" key with true or false'
                                      ' variable'.format(id)},
                            status=400)

def upload_draft_id(request, id):
    config = create_config()
    tmp = config.get('Directory-Section', 'temp')
    working_dir = '{}/yangvalidator/{}'.format(tmp, id)

    result = load_pre_setup(working_dir, id)
    if isinstance(result, HttpResponse):
        return result
    else:
        setup = result

    latest = setup.get('latest')
    results = []
    working_dirs = []
    try:
        for file in request.FILES.getlist('data'):
            while True:
                suffix = create_random_suffix()
                working_dir = '{}/yangvalidator/yangvalidator-v2-cache-{}'.format(tmp, suffix)
                if not os.path.exists(working_dir):
                    break
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
        return JsonResponse({'Error': 'Failed to upload and validate documents - {}'.format(e)}, status=400)
    return JsonResponse(results, safe=False)


def upload_file(request, id):
    config = create_config()
    yang_models = config.get('Directory-Section', 'save-file-dir')
    tmp = config.get('Directory-Section', 'temp')
    working_dir = '{}/yangvalidator/{}'.format(tmp, id)

    result = load_pre_setup(working_dir, id)
    if isinstance(result, HttpResponse):
        return result
    else:
        setup = result

    latest = setup.get('latest')
    get_from_options = setup.get('get-from-options')
    try:
        saved_files = []
        for file in request.FILES.getlist('data'):
            name, ext = os.path.splitext(file.name)
            logger.error(str(file.name))

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
                zf = ZipFile(zipfilename, 'r')
                zf.extractall(working_dir)
                saved_files.extend([filename for filename in zf.namelist() if filename.endswith('.yang')])
    except Exception as e:
        logger.exception('Error: {} : {}'.format(working_dir, e))
        if os.path.exists(working_dir):
            shutil.rmtree(working_dir)
        return JsonResponse({'Error': 'Failed to get yang files'}, status=400)
    return create_output(request, yang_models, None, latest, working_dir, saved_files,
                         choose_options=get_from_options)


def extract_files(request,  url: str, latest: bool, working_dir: str, remove_working_dir=True):
    config = create_config()
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
    json_body = {
        'modules-to-validate': {
            'user-modules': extracted_modules
        },
        'cache': working_dir.split('/')[-1]
    }
    if len(extracted_modules) == 0:
        if xym_response is None:
            response_args = {'data': {'Error': 'Failed to load any yang modules. Please provide at least one'
                                               ' yang module. File must have .yang extension'},
                             'status': 400}
        elif xym_response.get('stderr'):
            response_args = {'data': {'Error': 'Failed to xym parse url {}'.format(url),
                                               'xym': xym_response}}
        else:
            response_args = {'data': {'Error': 'No modules found using xym in url {}'.format(url),
                                               'xym': xym_response}}
        response = JsonResponse(**response_args)
    elif choose_options:
        existing_dependencies, found_repo_modules = checker.get_existing_dependencies()
        json_body['dependencies'] = {'missing': missing, 'existing': existing_dependencies}
        if len(missing) == 0 and not found_repo_modules:
            response = validate(request, xym_response, json_body)
        else:
            response = JsonResponse({'output': json_body}, status=202)
    elif latest:
        json_body['dependencies'] = {'repo-modules': checker.get_latest_revision()}
        response = validate(request, xym_response, json_body)
    elif len(missing) == 0:
        response = validate(request, xym_response, json_body)
    else:
        json_body['dependencies'] = {'missing': missing}
        if xym_response is not None:
            json_body['xym'] = xym_response
        response = JsonResponse({'output': json_body}, status=202)
    if not extracted_modules or latest or not missing:
        if os.path.exists(working_dir) and remove_working_dir:
            shutil.rmtree(working_dir)
    return response


def try_validate_and_load_data(request: WSGIRequest):
    """
    Check if request is POST and try to parse byte string to json format
    :param request: request sent from user
    :return: Parsed json string
    """
    if request.method != 'POST':
        raise IllegalMethodError(request.method)
    return json.loads(request.body)


def create_random_suffix():
    """
    Create random suffix to create new temp directory
    :return: suffix of random 8 letters
    """
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(8))


def check_missing_amount_one_only(missing: dict):
    for val in missing.values():
        if len(val) > 1:
            return False
    return True


if not os.path.exists('{}/yangvalidator'.format(create_config().get('Directory-Section', 'temp'))):
    os.mkdir('{}/yangvalidator'.format(create_config().get('Directory-Section', 'temp')))
