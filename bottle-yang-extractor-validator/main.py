#!/usr/bin/env python

import os, sys, cgi, argparse
from StringIO import StringIO
from subprocess import call, check_output, CalledProcessError
from tempfile import *
from shutil import *
from zipfile import *
from datetime import datetime
from functools import wraps
import logging

from xym import xym
import pyang
from bottle import route, run, install, template, request, response, static_file, error

# requests.packages.urllib3.disable_warnings()

__author__ = 'camoberg@cisco.com'
__copyright__ = "Copyright (c) 2016-2018, Carl Moberg, camoberg@cisco.com"
__license__ = "New-style BSD"
__email__ = "camoberg@cisco.com"
__version__ = "0.3.1"

yang_import_dir = '/var/tmp/yangmodules/extracted'
pyang_cmd = '/usr/local/bin/pyang'
yanglint_cmd = '/usr/local/bin/yanglint'
yanglint_version = check_output(yanglint_cmd + " --version", shell=True)
confdc_cmd = '/usr/local/bin/confdc'

debug = False

logger = logging.getLogger('yang-extractor-validator')
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('yangvalidator.log')
formatter = logging.Formatter('%(msg)s')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def log_to_logger(fn):
    '''
    Wrap a Bottle request so that a log line is emitted after it's handled.
    (This decorator can be extended to take the desired logger as a param.)
    '''
    @wraps(fn)
    def _log_to_logger(*args, **kwargs):
        request_time = datetime.now()
        actual_response = fn(*args, **kwargs)
        # modify this to log exactly what you need:
        logger.info('%s %s %s %s %s' % (request.remote_addr,
                                        request_time,
                                        request.method,
                                        request.url,
                                        response.status))
        return actual_response
    return _log_to_logger


def create_output(url):
    workdir = mkdtemp()
    results = {}

    result = StringIO()

    # Trickery to capture stderr from the xym tools for later use
    stderr_ = sys.stderr
    sys.stderr = result
    extracted_models = xym.xym(source_id = url, dstdir = workdir, srcdir = "", strict = True, strict_examples = False, debug_level = 0)
    sys.stderr = stderr_
    xym_stderr = result.getvalue()

    for em in extracted_models:
        pyang_stderr, pyang_output, confdc_stderr, yanglint_stderr = validate_yangfile(em, workdir)
        results[em] = { "pyang_stderr": cgi.escape(pyang_stderr),
                        "pyang_output": cgi.escape(pyang_output),
                        "xym_stderr": cgi.escape(xym_stderr),
                        "confdc_stderr": cgi.escape(confdc_stderr),
                        "yanglint_stderr": cgi.escape(yanglint_stderr) }

    rmtree(workdir)

    return results

def validate_yangfile(infilename, workdir):
    pyang_stderr = pyang_output = confdc_stderr = yanglint_stderr = ""
    infile = os.path.join(workdir, infilename)
    pyang_outfile = str(os.path.join(workdir, infilename) + '.pout')
    pyang_resfile = str(os.path.join(workdir, infilename) + '.pres')
    confdc_resfile = str(os.path.join(workdir, infilename) + '.cres')
    yanglint_resfile = str(os.path.join(workdir, infilename) + '.lres')

    presfp = open(pyang_resfile, 'w+')
    if infilename.startswith("ietf", 0):
        status = call([pyang_cmd, '-p', yang_import_dir, '-p', workdir, '--ietf', '-f', 'tree', infile, '-o', pyang_outfile], stderr = presfp)
        # Validate a Cisco YANG module that can start with 'Cisco' or 'cisco'.
    elif infilename.startswith("isco", 1):
        status = call([pyang_cmd, '-p', yang_import_dir, '-p', workdir, '--cisco', '-f', 'tree', infile, '-o', pyang_outfile], stderr = presfp)
    elif infilename.startswith("mef", 0):
        status = call([pyang_cmd, '-p', yang_import_dir, '-p', workdir, '--mef', '-f', 'tree', infile, '-o', pyang_outfile], stderr = presfp)
    elif infilename.startswith("ieee", 0):
        status = call([pyang_cmd, '-p', yang_import_dir, '-p', workdir, '--ieee', '-f', 'tree', infile, '-o', pyang_outfile], stderr = presfp)
    elif infilename.startswith("bbf", 0):
        status = call([pyang_cmd, '-p', yang_import_dir, '-p', workdir, '--bbf', '-f', 'tree', infile, '-o', pyang_outfile], stderr = presfp)
        # Default validation
    else:
        status = call([pyang_cmd, '-p', yang_import_dir, '-p', workdir, '-f', 'tree', infile, '-o', pyang_outfile], stderr = presfp)
                
    if os.path.isfile(pyang_outfile):
        outfp = open(pyang_outfile, 'r')
        pyang_output = str(outfp.read())
    else:
        pass

    presfp.seek(0)

    for line in presfp.readlines():
        pyang_stderr += os.path.basename(line)

    cresfp = open(confdc_resfile, 'w+')
    status = call([confdc_cmd, '-W', 'all', '--yangpath', workdir, '--yangpath', yang_import_dir, '-c', infile], stderr = cresfp)

    cresfp.seek(0)

    for line in cresfp.readlines():
        confdc_stderr += os.path.basename(line)


    yresfp = open(yanglint_resfile, 'w+')
    status = call([yanglint_cmd, '-i', '-p', workdir, '-p', yang_import_dir, '-V', infile], stderr = yresfp)

    yresfp.seek(0)

    for line in yresfp.readlines():
        yanglint_stderr += line


    return pyang_stderr, pyang_output, confdc_stderr, yanglint_stderr

@route('/')
@route('/validator')
def validator():
    return template('main', results = {}, versions = versions)

@route('/draft-validator', method="POST")
def upload_draft():
    results = {}
    savedfiles = []
    savedir = mkdtemp()

    uploaded_file = request.files.get("data")
    filepath = os.path.join(savedir, uploaded_file.raw_filename)
    uploaded_file.save(filepath)
    results = create_output(filepath)

    rmtree(savedir)

    return template('main', results = results, versions = versions)

@route('/validator', method="POST")
def upload_file():
    results = {}
    savedfiles = []
    savedir = mkdtemp()

    uploaded_files = request.files.getlist("data")

    for file in uploaded_files:
        name, ext = os.path.splitext(file.filename)

        if ext == ".yang":
            file.save(os.path.join(savedir, file.raw_filename))
            savedfiles.append(file.raw_filename)

        if ext == ".zip":
            zipfilename = os.path.join(savedir, file.filename)
            file.save(zipfilename)
            zf = ZipFile(zipfilename, "r")
            zf.extractall(savedir)
            for filename in zf.namelist():
                savedfiles.append(filename)

    for file in savedfiles:
        pyang_stderr, pyang_output, confdc_stderr, yanglint_stderr = validate_yangfile(file, savedir)
        results[file] = { "pyang_stderr": pyang_stderr, "pyang_output": pyang_output, "confdc_stderr": confdc_stderr, "yanglint_stderr": yanglint_stderr}

    rmtree(savedir)

    return template('main', results = results, versions = versions)

@route('/api/rfc/<rfc>')
def json_validate_rfc(rfc):
    response = []
    url = 'https://tools.ietf.org/rfc/rfc{!s}.txt'.format(rfc)
    results = create_output(url)
    return results

@route('/api/draft/<draft>')
def json_validate_draft(draft):
    response = []
    url = 'http://tools.ietf.org/id/{!s}'.format(draft)
    results = create_output(url)
    return results

@route('/api/versions')
def get_versions():
    return versions

@route('/rfc', method='GET')
def validate_rfc_param():
    rfc = request.query['number']
    url = 'https://tools.ietf.org/rfc/rfc{!s}.txt'.format(rfc)
    results = create_output(url)
    return template('result', results = results)

@route('/draft', method='GET')
def validate_draft_param():
    draft = request.query['name']
    url = 'http://tools.ietf.org/id/{!s}'.format(draft)
    results = create_output(url)
    return template('result', results = results)

@route('/rfc/<rfc>')
def validate_rfc(rfc):
    response = []
    url = 'https://tools.ietf.org/rfc/rfc{!s}.txt'.format(rfc)
    results = create_output(url)
    print "RESULTS", results
    return template('result', results = results)

@route('/draft/<draft>')
def validate_draft(draft):
    response = []
    url = 'http://www.ietf.org/id/{!s}'.format(draft)
    results = create_output(url)
    print "RESULTS", results
    return template('result', results = results)

@route('/static/:path#.+#', name='static')
def static(path):
    return static_file(path, root='static')

@route('/rest')
def rest():
    return(template('rest'))

@route('/about')
def about():
    return(template('about'))

@error(404)
def error404(error):
    return 'Nothing here, sorry.'

if __name__ == '__main__':
    port = 8080

    parser = argparse.ArgumentParser(description='A YANG fetching, extracting and validating web application.')
    parser.add_argument('-p', '--port', dest='port', type=int, help='Port to listen to (default is 8080)')
    parser.add_argument('-d', '--debug', help='Turn on debugging output', action="store_true")
    parser.add_argument('-c', '--confd-install-path', dest='confd_path', help='Path to ConfD')
    parser.add_argument('-y', '--yanglint-install-path', dest='yanglint_path', help='Path (install prefix) to yanglint')
    args = parser.parse_args()

    if args.port:
        port = args.port

    if args.debug:
        debug = True

    if args.confd_path:
        confd_path = args.confd_path
        confdc_cmd = confd_path + '/bin/confdc'

    if args.yanglint_path:
        yanglint_cmd = args.yanglint_path + '/bin/yanglint'

    install(log_to_logger)

    try:
        confdc_version = check_output(confdc_cmd + " --version", stderr=STDOUT, shell=True)
    except CalledProcessError:
        pass

    versions = {"validator_version": __version__, "pyang_version": pyang.__version__, "xym_version": xym.__version__, "confdc_version": confdc_version, "yanglint_version": yanglint_version }

    run(server='cherrypy', host='0.0.0.0', port=port)
