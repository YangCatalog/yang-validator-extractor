# Copyright The IETF Trust 2019, All Rights Reserved
# Copyright 2018 Cisco and its affiliates
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

"""Utility belt for working with ``pyang`` and ``pyangext``."""

__author__ = "Miroslav Kovac"
__copyright__ = "Copyright 2018 Cisco and its affiliates, Copyright The IETF Trust 2019, All Rights Reserved"
__license__ = "Apache License, Version 2.0"
__email__ = "miroslav.kovac@pantheon.tech"

import codecs
import io
from os.path import isfile

from pyang.context import Context
from pyang.error import error_codes
from pyang.repository import FileRepository
from pyang.yang_parser import YangParser
from pyang import statements
from .default_statements import StatementsDefault

DEFAULT_OPTIONS = {
    'path': [],
    'deviations': [],
    'features': [],
    'format': 'yang',
    'keep_comments': True,
    'no_path_recurse': False,
    'trim_yin': False,
    'yang_canonical': False,
    'yang_remove_unused_imports': False,
    # -- errors
    'ignore_error_tags': [],
    'ignore_errors': [],
    'list_errors': True,
    'print_error_code': False,
    'errors': [],
    'warnings': [code for code, desc in error_codes.items() if desc[0] > 4],
    'verbose': True,
}
"""Default options for pyang command line"""

_COPY_OPTIONS = [
    'canonical',
    'max_line_len',
    'max_identifier_len',
    'trim_yin',
    'lax_xpath_checks',
    'strict',
]
"""copy options to pyang context options"""


class objectify(object):  # pylint: disable=invalid-name
    """Utility for providing object access syntax (.attr) to dicts"""

    def __init__(self, *args, **kwargs):
        for entry in args:
            self.__dict__.update(entry)

        self.__dict__.update(kwargs)

    def __getattr__(self, _):
        return None

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value


def _parse_features_string(feature_str):
    if feature_str.find(':') == -1:
        return (feature_str, [])

    [module_name, rest] = feature_str.split(':', 1)
    if rest == '':
        return (module_name, [])

    features = rest.split(',')
    return (module_name, features)


def create_context(path='.', *options, **kwargs):
    """Generates a pyang context.

    The dict options and keyword arguments are similar to the command
    line options for ``pyang``. For ``plugindir`` use env var
    ``PYANG_PLUGINPATH``. For ``path`` option use the argument with the
    same name, or ``PYANG_MODPATH`` env var.

    Arguments:
        path (str): location of YANG modules.
            (Join string with ``os.pathsep`` for multiple locations).
            Default is the current working dir.
        *options: list of dicts, with options to be passed to context.
            See bellow.
        **kwargs: similar to ``options`` but have a higher precedence.
            See bellow.

    Keyword Arguments:
        print_error_code (bool): On errors, print the error code instead
            of the error message. Default ``False``.
        warnings (list): If contains ``error``, treat all warnings
            as errors, except any other error code in the list.
            If contains ``none``, do not report any warning.
        errors (list): Treat each error code container as an error.
        ignore_error_tags (list): Ignore error code.
            (For a list of error codes see ``pyang --list-errors``).
        ignore_errors (bool): Ignore all errors. Default ``False``.
        canonical (bool): Validate the module(s) according to the
            canonical YANG order. Default ``False``.
        yang_canonical (bool): Print YANG statements according to the
            canonical order. Default ``False``.
        yang_remove_unused_imports (bool): Remove unused import statements
            when printing YANG. Default ``False``.
        trim_yin (bool): In YIN input modules, trim whitespace
            in textual arguments. Default ``False``.
        lax_xpath_checks (bool): Lax check of XPath expressions.
            Default ``False``.
        strict (bool): Force strict YANG compliance. Default ``False``.
        max_line_len (int): Maximum line length allowed. Disabled by default.
        max_identifier_len (int): Maximum identifier length allowed.
            Disabled by default.
        features (list): Features to support, default all.
            Format ``<modname>:[<feature>,]*``.
        keep_comments (bool): Do not discard comments. Default ``True``.
        no_path_recurse (bool): Do not recurse into directories
            in the yang path. Default ``False``.

    Returns:
        pyang.Context: Context object for ``pyang`` usage
    """
    # deviations (list): Deviation module (NOT CURRENTLY WORKING).

    opts = objectify(DEFAULT_OPTIONS, *options, **kwargs)
    repo = FileRepository(path, no_path_recurse=opts.no_path_recurse)

    ctx = Context(repo)
    ctx.opts = opts

    for attr in _COPY_OPTIONS:
        setattr(ctx, attr, getattr(opts, attr))

    # make a map of features to support, per module (taken from pyang bin)
    for feature_name in opts.features:
        (module_name, features) = _parse_features_string(feature_name)
        ctx.features[module_name] = features

    # apply deviations (taken from pyang bin)
    for file_name in opts.deviations:
        with io.open(file_name, "r", encoding="utf-8") as fd:
            module = ctx.add_module(file_name, fd.read())
            if module is not None:
                ctx.deviation_modules.append(module)

    return ctx


def parse(text, ctx = None):
    """Parse a YANG statement into an Abstract Syntax subtree.

    Arguments:
        text (str): file name for a YANG module or text
        ctx (optional pyang.Context): context used to validate text

    Returns:
        pyang.statements.Statement: Abstract syntax subtree

    Note:
        The ``parse`` function can be used to parse small amounts of text.
        If yout plan to parse an entire YANG (sub)module, please use instead::

            ast = ctx.add_module(module_name, text_contet)

        It is also well known that ``parse`` function cannot solve
        YANG deviations yet.
    """
    parser = YangParser() # Similar names, but, this one is from PYANG library

    filename = 'parser-input'

    ctx_ = ctx or create_context()

    if isfile(text):
        filename = text
        text = codecs.open(filename, encoding="utf-8").read()

    # ensure reported errors are just from parsing
    # old_errors = ctx_.errors
    ctx_.errors = []

    ast = parser.parse(ctx_, filename, text)

    return ast


def restore_statements():
    statements_default = StatementsDefault()

    statements._validation_map = statements_default._validation_map
    statements.data_definition_keywords = statements_default.data_definition_keywords
    statements._validation_phases = statements_default._validation_phases
    statements._v_i_children = statements_default._v_i_children
    statements._v_i_children_keywords = statements_default._v_i_children_keywords
    statements._keyword_with_children = statements_default._keyword_with_children
    statements.data_keywords = statements_default.data_keywords
    statements._keywords_with_no_explicit_config = statements_default._keywords_with_no_explicit_config
    statements._copy_uses_keywords = statements_default._copy_uses_keywords
    statements._copy_augment_keywords = statements_default._copy_augment_keywords
    statements._refinements = statements_default._refinements
    statements._singleton_keywords = statements_default._singleton_keywords
    statements._deviate_delete_singleton_keywords = statements_default._deviate_delete_singleton_keywords
    statements._valid_deviations = statements_default._valid_deviations
    statements.STMT_CLASS_FOR_KEYWD = statements_default.STMT_CLASS_FOR_KEYWD

    statements._validation_variables = statements._validation_variables[0:2]
