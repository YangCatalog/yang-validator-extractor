# Copyright The IETF Trust 2019, All Rights Reserved
# Copyright 2015 Cisco and its affiliates
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

import cgi
import json
import logging
import os
import sys
from datetime import datetime, timezone
from io import StringIO
from shutil import *
from subprocess import CalledProcessError, call, check_output
from tempfile import *
from zipfile import *

import pyang
from django import forms
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render
from xym import xym

__author__ = "Miroslav Kovac, Carl Moberg"
__copyright__ = "Copyright 2015 Cisco and its affiliates, Copyright The IETF Trust 2019, All Rights Reserved"
__license__ = "Apache License, Version 2.0"
__email__ = "miroslav.kovac@pantheon.tech, camoberg@cisco.com"
__version__ = "0.4.0"


logger = logging.getLogger(__name__)
yang_import_dir = '/var/yang/all_modules'
pyang_cmd = '/usr/local/bin/pyang'
yanglint_cmd = '/usr/local/bin/yanglint'
yanglint_version = check_output(yanglint_cmd + " --version", shell=True).decode('utf-8').rstrip()
confdc_cmd = '/home/bottle/confd-6.7/bin/confdc'

debug = False
try:
    confdc_version = check_output(confdc_cmd + " --version", shell=True).decode('utf-8').rstrip()
except CalledProcessError:
    confdc_version = 'undefined'

versions = {"validator_version": __version__, "pyang_version": pyang.__version__, "xym_version": xym.__version__,
            "confdc_version": confdc_version, "yanglint_version": yanglint_version}


class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()


def index(request):
    context = versions
    context['results'] = {}
    return render(request, 'main.html', context)


def create_output(url, for_datatracker=False):
    workdir = mkdtemp()
    results = {}
    xym_res = {}
    result = StringIO()
    stdout = StringIO()

    # Trickery to capture stderr from the xym tools for later use
    stderr_ = sys.stderr
    stdout_ = sys.stdout
    sys.stderr = result
    sys.stdout = stdout
    extracted_models = xym.xym(source_id=url, dstdir=workdir, srcdir="", strict=True, strict_examples=False,
                               debug_level=0)
    xym_res['time'] = datetime.now(timezone.utc).isoformat()
    sys.stderr = stderr_
    sys.stdout = stdout_
    xym_stderr = result.getvalue()

    xym_res['stdout'] = stdout.getvalue()
    xym_res['stderr'] = xym_stderr
    xym_res['name'] = 'xym'
    xym_res['version'] = versions['xym_version']
    xym_res['code'] = None
    workdir_split = workdir.split('/')
    workdir_split[-1] = 'workdir-{}'.format(workdir_split[-1])
    workdir_to_json = '/'.join(workdir_split)
    xym_res['command'] = 'xym.xym(source_id="{}", dstdir="{}", srcdir="", strict=True, strict_examples=False, debug_level=0)'.format(url, workdir_to_json)

    if for_datatracker:
        results = {'extraction': xym_res}
        modules = []

    for em in extracted_models:
        file_name = em.split("@")[0].replace(".", "_")
        pyang_res, confdc_res, yanglint_res = validate_yangfile(em, workdir)
        if for_datatracker:
            modules.append({'name': em,
                            'checks': [pyang_res, confdc_res, yanglint_res]
                            })

        else:
            results[em] = {"pyang_stderr": cgi.escape(pyang_res['stderr']),
                           "pyang_output": cgi.escape(pyang_res['stdout']),
                           "xym_stderr": cgi.escape(xym_res['stderr']),
                           "confdc_stderr": cgi.escape(confdc_res['stderr']),
                           "yanglint_stderr": cgi.escape(yanglint_res['stderr']),
                           "name_split": file_name}
    if for_datatracker:
        results['modules'] = modules

    rmtree(workdir)
    return results


def validate_yangfile(infilename, workdir):
    logger.info('validating {}'.format(infilename))
    pyang_res = {}
    yanglint_res = {}
    confdc_res = {}
    pyang_stderr = pyang_output = confdc_output = yanglint_output = confdc_stderr = yanglint_stderr = ""
    infile = os.path.join(workdir, infilename)
    pyang_outfile = str(os.path.join(workdir, infilename) + '.pout')
    pyang_resfile = str(os.path.join(workdir, infilename) + '.pres')
    confdc_resfile = str(os.path.join(workdir, infilename) + '.cres')
    confdc_outfile = str(os.path.join(workdir, infilename) + '.cout')
    yanglint_resfile = str(os.path.join(workdir, infilename) + '.lres')
    yanglint_outfile = str(os.path.join(workdir, infilename) + '.lout')

    basic_append_p = []
    confdc_append = []
    pyang_command_to_json = []
    confdc_command_to_json = []
    libs = ''
    if os.path.exists(yang_import_dir):
        confdc_append = ['--yangpath', yang_import_dir]
        basic_append_p = ['-p', yang_import_dir]
        yang_import_dir_split = yang_import_dir.split('/')
        yang_import_dir_split[-1] = 'libs-{}'.format(yang_import_dir_split[-1])
        libs = '/'.join(yang_import_dir_split)
        pyang_command_to_json.extend([pyang_cmd, '-p', libs])
        confdc_command_to_json.extend([confdc_cmd, '--yangpath', libs])
    presfp = open(pyang_resfile, 'w+')
    poutresfp = open(pyang_outfile, 'w+')
    cmds = [pyang_cmd]
    cmds.extend(basic_append_p)
    workdir_split = workdir.split('/')
    workdir_split[-1] = 'workdir-{}'.format(workdir_split[-1])
    workdir_to_json = '/'.join(workdir_split)
    if infilename.startswith("ietf", 0):
        pyang_command = cmds + ['-p', workdir, '--ietf', infile]
        pyang_command_to_json.extend(['-p', workdir_to_json, '--ietf', '{}/{}'.format(workdir_to_json, infilename)])
        status = call(pyang_command, stdout=poutresfp, stderr=presfp)
        # Validate a Cisco YANG module that can start with 'Cisco' or 'cisco'.
    elif infilename.startswith("isco", 1):
        pyang_command = cmds + ['-p', workdir, '--cisco',infile]
        pyang_command_to_json.extend(['-p', workdir_to_json, '--cisco', '{}/{}'.format(workdir_to_json, infilename)])
        status = call(pyang_command, stdout=poutresfp, stderr=presfp)
    elif infilename.startswith("mef", 0):
        pyang_command = cmds + ['-p', workdir, '--mef', infile]
        pyang_command_to_json.extend(['-p', workdir_to_json, '--mef', '{}/{}'.format(workdir_to_json, infilename)])
        status = call(pyang_command, stdout=poutresfp, stderr=presfp)
    elif infilename.startswith("ieee", 0):
        pyang_command = cmds + ['-p', workdir, '--ieee', infile]
        pyang_command_to_json.extend(['-p', workdir_to_json, '--ieee', '{}/{}'.format(workdir_to_json, infilename)])
        status = call(pyang_command, stdout=poutresfp, stderr=presfp)
    elif infilename.startswith("bbf", 0):
        pyang_command = cmds + ['-p', workdir, '--bbf', infile]
        pyang_command_to_json.extend(['-p', workdir_to_json, '--bbf', '{}/{}'.format(workdir_to_json, infilename)])
        status = call(pyang_command, stdout=poutresfp, stderr=presfp)
        # Default validation
    else:
        pyang_command = cmds + ['-p', workdir, infile]
        pyang_command_to_json.extend(['-p', workdir_to_json, '{}/{}'.format(workdir_to_json, infilename)])
        status = call(pyang_command, stdout=poutresfp, stderr=presfp)
    pyang_res['time'] = datetime.now(timezone.utc).isoformat()
    if os.path.isfile(pyang_outfile):
        poutresfp.seek(0)
        for line in poutresfp.readlines():
            pyang_output += os.path.basename(line)
    else:
        pass
    pyang_res['stdout'] = pyang_output
    presfp.seek(0)
    poutresfp.close()

    for line in presfp.readlines():
        pyang_stderr += os.path.basename(line)
    pyang_res['stderr'] = pyang_stderr
    pyang_res['name'] = 'pyang'
    pyang_res['version'] = versions['pyang_version']
    pyang_res['code'] = status
    pyang_res['command'] = ' '.join(pyang_command_to_json)
    logger.info(' '.join(pyang_command))

    cresfp = open(confdc_resfile, 'w+')
    cmds = [confdc_cmd, '-f', workdir, '-W', 'all']
    cmds.extend(confdc_append)
    confdc_command = cmds + ['-c', infile]
    confdc_command_to_json.extend(['-f', workdir_to_json, '-W', 'all', '-c', '{}/{}'.format(workdir_to_json, infilename)])
    outfp = open(confdc_outfile, 'w+')
    status = call(confdc_command, stdout=outfp, stderr=cresfp)

    confdc_res['time'] = datetime.now(timezone.utc).isoformat()

    if os.path.isfile(confdc_outfile):
        outfp.seek(0)
        for line in outfp.readlines():
            confdc_output += os.path.basename(line)
    else:
        pass
    confdc_res['stdout'] = confdc_output
    outfp.close()
    cresfp.seek(0)

    for line in cresfp.readlines():
        confdc_stderr += os.path.basename(line)
    confdc_res['stderr'] = confdc_stderr
    confdc_res['name'] = 'confdc'
    confdc_res['version'] = versions['confdc_version']
    confdc_res['code'] = status
    confdc_res['command'] = ' '.join(confdc_command_to_json)
    logger.info(' '.join(confdc_command))

    yresfp = open(yanglint_resfile, 'w+')
    cmds = [yanglint_cmd, '-i', '-p', workdir]
    cmds.extend(basic_append_p)
    yanglint_command = cmds + ['-V', infile]
    yanglint_command_to_json = [yanglint_cmd, '-i']
    if libs != '':
        yanglint_command_to_json.extend(['-p', libs])
    yanglint_command_to_json = ['-p', workdir_to_json, '-V', '{}/{}'.format(workdir_to_json, infilename)]
    outfp = open(yanglint_outfile, 'w+')
    status = call(yanglint_command, stdout=outfp, stderr=yresfp)
    yanglint_res['time'] = datetime.now(timezone.utc).isoformat()

    if os.path.isfile(yanglint_outfile):
        outfp.seek(0)
        for line in outfp.readlines():
            yanglint_output += os.path.basename(line)
    else:
        pass
    yanglint_res['stdout'] = yanglint_output

    yresfp.seek(0)

    for line in yresfp.readlines():
        yanglint_stderr += line
    outfp.close()
    yanglint_res['stderr'] = yanglint_stderr
    yanglint_res['name'] = 'yanglint'
    yanglint_res['version'] = versions['yanglint_version']
    yanglint_res['code'] = status
    yanglint_res['command'] = ' '.join(yanglint_command_to_json)
    logger.info(' '.join(yanglint_command))

    return pyang_res, confdc_res, yanglint_res


def upload_draft(request):
    context = versions
    context['results'] = {}
    savedir = mkdtemp()

    for file in request.FILES.getlist('data'):
        filepath = os.path.join(savedir, file.name)
        with open(filepath, 'wb+') as f:
            for chunk in file.chunks():
                f.write(chunk)
        context['results'] = create_output(filepath)

    rmtree(savedir)
    return render(request, 'main.html', context)


def upload_file(request):
    context = versions
    context['results'] = {}
    savedfiles = []
    savedir = mkdtemp()

    for file in request.FILES.getlist('data'):
        name, ext = os.path.splitext(file.name)

        if ext == ".yang":
            with open(os.path.join(savedir, file.name), 'wb+') as f:
                for chunk in file.chunks():
                    f.write(chunk)
            savedfiles.append(file.name)

        if ext == ".zip":
            zipfilename = os.path.join(savedir, file.name)
            with open(zipfilename, 'wb+') as f:
                for chunk in file.chunks():
                    f.write(chunk)
            zf = ZipFile(zipfilename, "r")
            zf.extractall(savedir)
            for filename in zf.namelist():
                savedfiles.append(filename)

    for file in savedfiles:
        file_name = file.split("@")[0].replace(".", "_")
        pyang_res, confdc_res, yanglint_res = validate_yangfile(file, savedir)
        context['results'][file] = {"pyang_stderr": pyang_res['stderr'], "pyang_output": pyang_res['stdout'], "confdc_stderr": confdc_res['stderr'],
                         "yanglint_stderr": yanglint_res['stderr'], "name_split": file_name}

    rmtree(savedir)

    return render(request, 'main.html', context)


def json_validate_rfc(request, rfc):
    url = 'https://tools.ietf.org/rfc/rfc{!s}.txt'.format(rfc)
    results = create_output(url)
    results = json.dumps(results, cls=DjangoJSONEncoder)
    return HttpResponse(results, content_type='application/json')


def json_validate_draft(request, draft):
    url = 'http://tools.ietf.org/id/{!s}'.format(draft)
    results = create_output(url)
    results = json.dumps(results, cls=DjangoJSONEncoder)
    return HttpResponse(results, content_type='application/json')


def datatracker_rfc(request):
    documents = []
    rfcs = request.GET.getlist('doc')
    for doc in rfcs:
        url = 'https://tools.ietf.org/rfc/rfc{!s}.txt'.format(doc)
        results = create_output(url, for_datatracker=True)
        results["name"] = doc
        documents.append(results)
    result = {"yangvalidator-version": versions['validator_version'],
              "documents": documents}
    results = json.dumps(result, cls=DjangoJSONEncoder)
    return HttpResponse(results, content_type='application/json')


def datatracker_draft(request):
    documents = []
    drafts = request.GET.getlist('doc')
    for doc in drafts:
        url = 'http://tools.ietf.org/id/{!s}'.format(doc)
        results = create_output(url, for_datatracker=True)
        results["name"] = doc
        documents.append(results)
    result = {"yangvalidator-version": versions['validator_version'],
              "documents": documents}
    results = json.dumps(result, cls=DjangoJSONEncoder)
    return HttpResponse(results, content_type='application/json')


def get_versions(request):
    return versions


def validate_rfc_param(request):
    rfc = request.GET['number']
    url = 'https://tools.ietf.org/rfc/rfc{!s}.txt'.format(rfc)
    results = {}
    results['results'] = create_output(url)
    return render(request, 'result.html', results)


def validate_draft_param(request):
    draft = request.GET['name']
    url = 'http://tools.ietf.org/id/{!s}'.format(draft)
    results = {}
    results['results'] = create_output(url)
    return render(request, 'result.html', results)


def validate_rfc(request, rfc):
    url = 'https://tools.ietf.org/rfc/rfc{!s}.txt'.format(rfc)
    results = {}
    results['results'] = create_output(url)
    return render(request, 'main.html', results)


def validate_draft(request, draft):
    url = 'http://www.ietf.org/id/{!s}'.format(draft)
    results = {}
    results['results'] = create_output(url)
    return render(request, 'main.html', results)


def rest(request):
    return render(request, 'rest.html')


def about(request):
    return render(request, 'about.html')

