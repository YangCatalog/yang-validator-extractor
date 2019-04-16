import cgi
import json
import logging
import os
import sys
from io import StringIO
from shutil import *
from subprocess import CalledProcessError, call, check_output
from tempfile import *
from zipfile import *

import pyang
from django.core.serializers.json import DjangoJSONEncoder
from django import forms
from django.http import HttpResponse
from django.shortcuts import render
from xym import xym

__author__ = "Miroslav Kovac, Carl Moberg"
__copyright__ = "Copyright 2019 Cisco and its affiliates"
__license__ = "Apache License, Version 2.0"
__email__ = "miroslav.kovac@pantheon.tech, camoberg@cisco.com"
__version__ = "0.4.0"


logger = logging.getLogger(__name__)
yang_import_dir = '/var/tmp/yangmodules/extracted'
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
    print(context)
    return render(request, 'main.html', context)


def create_output(url):
    workdir = mkdtemp()
    results = {}
    results = {}

    result = StringIO()

    # Trickery to capture stderr from the xym tools for later use
    stderr_ = sys.stderr
    sys.stderr = result
    extracted_models = xym.xym(source_id=url, dstdir=workdir, srcdir="", strict=True, strict_examples=False,
                               debug_level=0)
    sys.stderr = stderr_
    xym_stderr = result.getvalue()

    for em in extracted_models:
        file_name = em.split("@")[0].replace(".", "_")
        pyang_stderr, pyang_output, confdc_stderr, yanglint_stderr = validate_yangfile(em, workdir)
        results[em] = {"pyang_stderr": cgi.escape(pyang_stderr),
                                  "pyang_output": cgi.escape(pyang_output),
                                  "xym_stderr": cgi.escape(xym_stderr),
                                  "confdc_stderr": cgi.escape(confdc_stderr),
                                  "yanglint_stderr": cgi.escape(yanglint_stderr),
                                  "name_split": file_name}

    rmtree(workdir)
    return results


def validate_yangfile(infilename, workdir):
    pyang_stderr = pyang_output = confdc_stderr = yanglint_stderr = ""
    infile = os.path.join(workdir, infilename)
    pyang_outfile = str(os.path.join(workdir, infilename) + '.pout')
    pyang_resfile = str(os.path.join(workdir, infilename) + '.pres')
    confdc_resfile = str(os.path.join(workdir, infilename) + '.cres')
    yanglint_resfile = str(os.path.join(workdir, infilename) + '.lres')

    basic_append_p = []
    confdc_append = []
    if os.path.exists(yang_import_dir):
        confdc_append = ['--yangpath', yang_import_dir]
        basic_append_p = ['-p', yang_import_dir]
    presfp = open(pyang_resfile, 'w+')
    cmds = [pyang_cmd]
    cmds.extend(basic_append_p)
    if infilename.startswith("ietf", 0):
        status = call(
            cmds + ['-p', workdir, '--ietf', '-f', 'tree', infile, '-o', pyang_outfile], stderr=presfp)
        # Validate a Cisco YANG module that can start with 'Cisco' or 'cisco'.
    elif infilename.startswith("isco", 1):
        status = call(
            cmds + ['-p', workdir, '--cisco', '-f', 'tree', infile, '-o', pyang_outfile], stderr=presfp)
    elif infilename.startswith("mef", 0):
        status = call(
            cmds + ['-p', workdir, '--mef', '-f', 'tree', infile, '-o', pyang_outfile], stderr=presfp)
    elif infilename.startswith("ieee", 0):
        status = call(
            cmds + ['-p', workdir, '--ieee', '-f', 'tree', infile, '-o', pyang_outfile], stderr=presfp)
    elif infilename.startswith("bbf", 0):
        status = call(
            cmds + ['-p', workdir, '--bbf', '-f', 'tree', infile, '-o', pyang_outfile], stderr=presfp)
        # Default validation
    else:
        status = call(cmds + ['-p', workdir, '-f', 'tree', infile, '-o', pyang_outfile], stderr=presfp)

    if os.path.isfile(pyang_outfile):
        outfp = open(pyang_outfile, 'r')
        pyang_output = str(outfp.read())
    else:
        pass

    presfp.seek(0)

    for line in presfp.readlines():
        pyang_stderr += os.path.basename(line)

    cresfp = open(confdc_resfile, 'w+')
    cmds = [confdc_cmd, '-f', workdir, '-W', 'all']
    cmds.extend(confdc_append)
    status = call(cmds + ['-c', infile], stderr=cresfp)

    cresfp.seek(0)

    for line in cresfp.readlines():
        confdc_stderr += os.path.basename(line)

    yresfp = open(yanglint_resfile, 'w+')
    cmds = [yanglint_cmd, '-i', '-p', workdir]
    cmds.extend(basic_append_p)
    status = call(cmds + ['-V', infile], stderr=yresfp)

    yresfp.seek(0)

    for line in yresfp.readlines():
        yanglint_stderr += line

    return pyang_stderr, pyang_output, confdc_stderr, yanglint_stderr


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

    #uploaded_files = request.FILES.getlist("data")

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
        pyang_stderr, pyang_output, confdc_stderr, yanglint_stderr = validate_yangfile(file, savedir)
        context['results'][file] = {"pyang_stderr": pyang_stderr, "pyang_output": pyang_output, "confdc_stderr": confdc_stderr,
                         "yanglint_stderr": yanglint_stderr, "name_split": file_name}

    rmtree(savedir)

    return render(request, 'main.html', context)


def json_validate_rfc(request, rfc):
    response = []
    url = 'https://tools.ietf.org/rfc/rfc{!s}.txt'.format(rfc)
    results = create_output(url)
    results = json.dumps(results, cls=DjangoJSONEncoder)
    return HttpResponse(results, content_type='application/json')

def json_validate_draft(request, draft):
    response = []
    url = 'http://tools.ietf.org/id/{!s}'.format(draft)
    results = create_output(url)
    results = json.dumps(results, cls=DjangoJSONEncoder)
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
    response = []
    url = 'https://tools.ietf.org/rfc/rfc{!s}.txt'.format(rfc)
    results = {}
    results['results'] = create_output(url)
    return render(request, 'main.html', results)


def validate_draft(request, draft):
    response = []
    url = 'http://www.ietf.org/id/{!s}'.format(draft)
    results = {}
    results['results'] = create_output(url)
    return render(request, 'main.html', results)


def rest(request):
    return render(request, 'rest.html')


def about(request):
    return render(request, 'about.html')

