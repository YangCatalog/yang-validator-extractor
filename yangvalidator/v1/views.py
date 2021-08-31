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
import glob
import io
import json
import logging
import os
import random
import shutil
import string
import sys
from datetime import datetime, timezone
from io import StringIO
from subprocess import CalledProcessError, call, check_output
from tempfile import *
from zipfile import ZipFile

import jinja2
import pyang
from django import forms
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render
from pyang import error, plugin
from pyang.plugins.depend import emit_depend
from xym import __version__ as xym_version
from xym import xym

from yangvalidator.create_config import create_config
from yangvalidator.yangParser import create_context, restore_statements

__author__ = "Miroslav Kovac, Carl Moberg"
__copyright__ = "Copyright 2015 Cisco and its affiliates, Copyright The IETF Trust 2019, All Rights Reserved"
__license__ = "Apache License, Version 2.0"
__email__ = "miroslav.kovac@pantheon.tech, camoberg@cisco.com"
__version__ = "1.1.0"

logger = logging.getLogger(__name__)
yang_import_dir = '/var/yang/all_modules'
pyang_cmd = '/usr/local/bin/pyang'
yanglint_cmd = '/usr/local/bin/yanglint'
confdc_cmd = '/home/bottle/confd-7.5/bin/confdc'
yangdump_cmd = '/usr/bin/yangdump-pro'

debug = False

try:
    yanglint_version = check_output(yanglint_cmd + " --version", shell=True).decode('utf-8').rstrip()
except CalledProcessError:
    yanglint_version = 'undefined'

try:
    confdc_version = check_output(confdc_cmd + " --version", shell=True).decode('utf-8').rstrip()
except CalledProcessError:
    confdc_version = 'undefined'

try:
    yangdump_version = check_output(yangdump_cmd + " --version", shell=True).decode('utf-8').strip()
except CalledProcessError:
    yangdump_version = 'undefined'

versions = {"validator_version": __version__, "pyang_version": pyang.__version__, "xym_version": xym_version,
            "confdc_version": confdc_version, "yanglint_version": yanglint_version,
            "yangdump_version": yangdump_version}


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
    try:
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
        xym_res[
            'command'] = 'xym.xym(source_id="{}", dstdir="{}", srcdir="", strict=True, strict_examples=False, debug_level=0)'.format(
            url, workdir_to_json)

        if for_datatracker:
            results = {'extraction': xym_res}
            modules = []

        for em in extracted_models:
            file_name = em.split("@")[0].replace(".", "_")
            pyang_res, confdc_res, yanglint_res, yangdump_res = validate_yangfile(em, workdir)
            if for_datatracker:
                modules.append({'name': em,
                                'checks': [pyang_res, confdc_res, yanglint_res, yangdump_res]
                                })

            else:
                results[em] = {"pyang_stderr": cgi.escape(pyang_res['stderr']),
                            "pyang_output": cgi.escape(pyang_res['stdout']),
                            "xym_stderr": cgi.escape(xym_res['stderr']),
                            "confdc_stderr": cgi.escape(confdc_res['stderr']),
                            "yanglint_stderr": cgi.escape(yanglint_res['stderr']),
                            "yangdump_stderr": cgi.escape(yangdump_res['stderr']),
                            "name_split": file_name}
        if for_datatracker:
            results['modules'] = modules
    except Exception as e:
        logger.error('Error: {}'.format(e))
    finally:
        if os.path.exists(workdir):
            shutil.rmtree(workdir)

    return results


def print_pyang_output(ctx):
    err = ''
    out = ''
    for (epos, etag, eargs) in ctx.errors:
        elevel = error.err_level(etag)
        if error.is_warning(elevel):
            kind = "warning"
        else:
            kind = "error"

        err += str(epos) + ': %s: ' % kind + \
               error.err_to_str(etag, eargs) + '\n'
    return err, out


def copy_dependencies(f):
    config = create_config()
    yang_models = config.get('Directory-Section', 'save-file-dir')
    tmp = config.get('Directory-Section', 'temp')
    out = f.getvalue()
    logger.info('dependencies received in following format: {}'.format(out))
    letters = string.ascii_letters
    suffix = ''.join(random.choice(letters) for i in range(8))
    dep_dir = '{}/yangvalidator-dependencies-{}'.format(tmp, suffix)
    os.mkdir(dep_dir)
    if len(out.split(':')) == 2:
        dependencies = out.split(':')[1].strip().split(' ')
    else:
        dependencies = []
    for dep in dependencies:
        for file in glob.glob(r'{}/{}@*.yang'.format(yang_models, dep)):
            shutil.copy(file, dep_dir)
    return dep_dir


def validate_yangfile(infilename, workdir):
    logger.info('validating {}'.format(infilename))
    pyang_res = {}
    yanglint_res = {}
    confdc_res = {}
    yangdump_res = {}
    confdc_output = yanglint_output = confdc_stderr = yanglint_stderr = yangdump_output = yangdump_stderr = ""
    infile = os.path.join(workdir, infilename)
    confdc_resfile = str(os.path.join(workdir, infilename) + '.cres')
    confdc_outfile = str(os.path.join(workdir, infilename) + '.cout')
    yanglint_resfile = str(os.path.join(workdir, infilename) + '.lres')
    yanglint_outfile = str(os.path.join(workdir, infilename) + '.lout')
    yangdump_resfile = str(os.path.join(workdir, infilename) + '.ypres')
    yangdump_outfile = str(os.path.join(workdir, infilename) + '.ypout')

    basic_append_p = []
    pyang_command = []
    pyang_command_to_json = []
    confdc_command_to_json = []

    pyang_context_directories = [workdir]
    libs = ''
    try:
        if os.path.exists(yang_import_dir):
            basic_append_p = ['-p', yang_import_dir]
            pyang_context_directories.append(yang_import_dir)
            yang_import_dir_split = yang_import_dir.split('/')
            yang_import_dir_split[-1] = 'libs-{}'.format(yang_import_dir_split[-1])
            libs = '/'.join(yang_import_dir_split)
            pyang_command_to_json.extend([pyang_cmd, '-p', libs])
            confdc_command_to_json.extend([confdc_cmd, '--yangpath', libs])
        cmds = [pyang_cmd]
        cmds.extend(basic_append_p)

        # Plugins array must be emptied before plugin init
        plugin.plugins = []
        plugin.init([])
        ctx = create_context(':'.join(pyang_context_directories))

        ctx.opts.lint_namespace_prefixes = []
        ctx.opts.lint_modulename_prefixes = []
        if infilename.startswith("ietf", 0):
            ctx.opts.ietf = True
            pyang_command = cmds + ['-p', workdir, '--ietf', infile]
            pyang_command_to_json.extend(['-p', workdir, '--ietf', infile])
        elif infilename.startswith("mef", 0):
            ctx.opts.mef = True
            pyang_command = cmds + ['-p', workdir, '--mef', infile]
            pyang_command_to_json.extend(['-p', workdir, '--mef', infile])
        elif infilename.startswith("ieee", 0):
            ctx.opts.ieee = True
            pyang_command = cmds + ['-p', workdir, '--ieee', infile]
            pyang_command_to_json.extend(['-p', workdir, '--ieee', infile])
        elif infilename.startswith("bbf", 0):
            ctx.opts.bbf = True
            pyang_command = cmds + ['-p', workdir, '--bbf', infile]
            pyang_command_to_json.extend(['-p', workdir, '--bbf', infile])
        pyang_res['time'] = datetime.now(timezone.utc).isoformat()

        ctx.opts.depend_recurse = True
        ctx.opts.depend_ignore = []
        for p in plugin.plugins:
            p.setup_ctx(ctx)
        m = []
        with open(infile, 'r', encoding="utf-8") as yang_file:
            module = yang_file.read()
            if module is None:
                logger.info('no module provided')
            m = ctx.add_module(infile, module)
            if m is None:
                m = []
            else:
                m = [m]
        ctx.validate()

        f = io.StringIO()
        emit_depend(ctx, m, f)
        dep_dir = copy_dependencies(f)

        pyang_stderr, pyang_output = print_pyang_output(ctx)

        # Data cleanup due to a recursion problem
        restore_statements()
        del ctx

        pyang_res['stdout'] = pyang_output
        pyang_res['stderr'] = pyang_stderr
        pyang_res['name'] = 'pyang'
        pyang_res['version'] = versions['pyang_version']
        pyang_res['code'] = 0 if not pyang_stderr else 1
        pyang_res['command'] = ' '.join(pyang_command_to_json)
        logger.info(' '.join(pyang_command))

        cresfp = open(confdc_resfile, 'w+')
        fxsfile = infile.replace('.yang', '.fxs')
        cmds = [confdc_cmd, '-o', fxsfile, '-W', 'all']
        cmds.extend(['--yangpath', dep_dir])
        cmds.extend(['--yangpath', workdir])
        confdc_command = cmds + ['-c', infile]
        confdc_command_to_json.extend(['-o', fxsfile, '-W', 'all', '-c', infile])
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
        cmds.extend(['-p', dep_dir])
        yanglint_command = cmds + ['-V', infile]
        yanglint_command_to_json = [yanglint_cmd, '-i']
        if libs != '':
            yanglint_command_to_json.extend(['-p', libs])
        yanglint_command_to_json = ['-p', workdir, '-V', infile]
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
        yresfp.close()
        yanglint_res['stderr'] = yanglint_stderr
        yanglint_res['name'] = 'yanglint'
        yanglint_res['version'] = versions['yanglint_version']
        yanglint_res['code'] = status
        yanglint_res['command'] = ' '.join(yanglint_command_to_json)
        logger.info(' '.join(yanglint_command))

        context = {'path': dep_dir}

        path, filename = os.path.split(
            os.path.dirname(__file__) + '/../templates/yangdump-pro-yangvalidator.conf')
        rendered_config_text = jinja2.Environment(loader=jinja2.FileSystemLoader(path or './')
                                                ).get_template(filename).render(context)
        conf_yangdump_dir = '{}-conf'.format(dep_dir)
        os.mkdir(conf_yangdump_dir)
        yangdump_config_file = '{}/yangdump-pro-yangvalidator.conf'
        with open(yangdump_config_file.format(conf_yangdump_dir), 'w') as ff:
            ff.write(rendered_config_text)
        ypresfp = open(yangdump_resfile, 'w+')
        cmds = [yangdump_cmd, '--quiet-mode', '--config', yangdump_config_file]
        yangdump_command = cmds + [infile]
        yangdump_command_to_json = yangdump_command

        ypoutfp = open(yangdump_outfile, 'w+')
        status = call(yangdump_command, stdout=ypoutfp, stderr=ypresfp)
        yangdump_res['time'] = datetime.now(timezone.utc).isoformat()

        if os.path.isfile(yangdump_outfile):
            ypoutfp.seek(0)
            for line in ypoutfp.readlines():
                yangdump_output += os.path.basename(line)
        else:
            pass
        yangdump_res['stdout'] = yangdump_output

        ypresfp.seek(0)

        for line in ypresfp.readlines():
            yangdump_stderr += line
        ypoutfp.close()
        ypresfp.close()
        yangdump_res['stderr'] = yangdump_stderr
        yangdump_res['name'] = 'yangdump-pro'
        yangdump_res['version'] = versions['yangdump_version']
        yangdump_res['code'] = status
        yangdump_res['command'] = ' '.join(yangdump_command_to_json)
        logger.info(' '.join(yangdump_command))

    except Exception as e:
        logger.error('Error: {}'.format(e))

    finally:
        logger.info('Removing temporary directories')

        if os.path.exists(dep_dir):
            shutil.rmtree(dep_dir)
        if os.path.exists(conf_yangdump_dir):
            shutil.rmtree(conf_yangdump_dir)

    return pyang_res, confdc_res, yanglint_res, yangdump_res


def upload_draft(request):
    context = versions
    context['results'] = {}
    savedir = mkdtemp()

    try:
        for file in request.FILES.getlist('data'):
            filepath = os.path.join(savedir, file.name)
            with open(filepath, 'wb+') as f:
                for chunk in file.chunks():
                    f.write(chunk)
            context['results'] = create_output(filepath)
    except Exception as e:
        logger.error('Error: %s : %s' % (savedir, e))
    finally:
        if os.path.exists(savedir):
            shutil.rmtree(savedir)

    return render(request, 'main.html', context)


def upload_file(request):
    context = versions
    context['results'] = {}
    savedfiles = []
    savedir = mkdtemp()

    try:
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
                savedfiles = [filename for filename in zf.namelist() if filename.endswith('.yang')]

        for file in savedfiles:
            file_name = file.split("@")[0].replace(".", "_")
            pyang_res, confdc_res, yanglint_res, yangdump_res = validate_yangfile(file, savedir)
            context['results'][file] = {"pyang_stderr": pyang_res['stderr'], "pyang_output": pyang_res['stdout'],
                                        "confdc_stderr": confdc_res['stderr'],
                                        "yanglint_stderr": yanglint_res['stderr'],
                                        "yangdump_stderr": yangdump_res['stderr'], "name_split": file_name}
    except Exception as e:
        logger.error('Error: %s : %s' % (savedir, e))
    finally:
        if os.path.exists(savedir):
            shutil.rmtree(savedir)

    return render(request, 'main.html', context)


def json_validate_rfc(request, rfc):
    logger.info('validating rfc {}'.format(rfc))
    url = 'https://tools.ietf.org/rfc/rfc{!s}.txt'.format(rfc)
    results = create_output(url)
    results = json.dumps(results, cls=DjangoJSONEncoder)
    return HttpResponse(results, content_type='application/json')


def json_validate_draft(request, draft):
    if draft.endswith('.txt'):
        draft = draft[:-4]
    logger.info('validating draft {}'.format(draft))
    url = 'https://tools.ietf.org/id/{!s}.txt'.format(draft)
    results = create_output(url)
    results = json.dumps(results, cls=DjangoJSONEncoder)
    return HttpResponse(results, content_type='application/json')


def datatracker_rfc(request):
    documents = []
    rfcs = request.GET.getlist('doc')
    for doc in rfcs:
        logger.info('validating rfc {}'.format(doc))
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
        if doc.endswith('.txt'):
            doc = doc[:-4]
        logger.info('validating draft {}'.format(doc))
        url = 'http://tools.ietf.org/id/{!s}.txt'.format(doc)
        results = create_output(url, for_datatracker=True)
        results["name"] = doc
        documents.append(results)
    result = {"yangvalidator-version": versions['validator_version'],
              "documents": documents}
    results = json.dumps(result, cls=DjangoJSONEncoder)
    return HttpResponse(results, content_type='application/json')


def get_versions(request):
    results = json.dumps(versions, cls=DjangoJSONEncoder)
    return HttpResponse(results, content_type='application/json')


def validate_rfc_param(request):
    rfc = request.GET['number']
    logger.info('validating rfc {}'.format(rfc))
    url = 'https://tools.ietf.org/rfc/rfc{!s}.txt'.format(rfc)
    results = {}
    results['results'] = create_output(url)
    return render(request, 'result.html', results)


def validate_draft_param(request):
    draft = request.GET['name']
    if draft.endswith('.txt'):
        draft = draft[:-4]
    logger.info('validating draft {}'.format(draft))
    url = 'http://tools.ietf.org/id/{!s}.txt'.format(draft)
    results = {}
    results['results'] = create_output(url)
    return render(request, 'result.html', results)


def validate_rfc(request, rfc):
    logger.info('validating rfc {}'.format(rfc))
    url = 'https://tools.ietf.org/rfc/rfc{!s}.txt'.format(rfc)
    results = {}
    results['results'] = create_output(url)
    return render(request, 'main.html', results)


def validate_draft(request, draft):
    if draft.endswith('.txt'):
        draft = draft[:-4]
    logger.info('validating draft {}'.format(draft))
    url = 'https://tools.ietf.org/id/{!s}.txt'.format(draft)
    results = {}
    results['results'] = create_output(url)
    return render(request, 'main.html', results)


def rest(request):
    return render(request, 'rest.html')


def about(request):
    return render(request, 'about.html')


def ping(request):
    logger.info('Ping from healthcheck')
    req_data = json.loads(request.body)

    if req_data['input']['data'] == 'ping':
        return HttpResponse(json.dumps({'info': 'Success'}, cls=DjangoJSONEncoder),
                            content_type='application/json', status=200)
    else:
        return HttpResponse(json.dumps({'error': 'Bad request body'}, cls=DjangoJSONEncoder),
                            content_type='application/json', status=400)
