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

# According to django-stubs, assertJSONEqual cannot take bytes as the first arg.
# This should probably be fixed in upstream django-stubs
# pyright: reportGeneralTypeIssues=false

__author__ = 'Richard Zilincik'
__copyright__ = 'Copyright The IETF Trust 2021, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'richard.zilincik@pantheon.tech'

import json
import os
from copy import deepcopy
from unittest import mock

from django.test import RequestFactory, SimpleTestCase

import yangvalidator.v2.views as v


class TestViews(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        cls.factory = RequestFactory()
        resource_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')
        for parser in ('Confd', 'YangdumpPro'):
            patcher = mock.patch(f'yangvalidator.v2.views.{parser}Parser', mock.MagicMock)
            mock_parser = patcher.start()
            cls.addClassCleanup(patcher.stop)
            mock_parser.parse_module = lambda self: 'test'
        ownership_patcher = mock.patch('yangvalidator.v2.views.change_ownership_recursive')
        cls.mock_ownership = ownership_patcher.start()
        cls.addClassCleanup(ownership_patcher.stop)
        cls.mock_ownership.return_value = None
        with open(os.path.join(resource_path, 'payloads.json')) as f:
            cls.payloads_data = json.load(f)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_validate_not_json(self):
        result = v.validate(self.factory.post('/yangvalidator/v2/validate'))

        self.assertEqual(result.status_code, 400)
        try:
            json.loads('not json')
        except ValueError as e:
            self.assertJSONEqual(
                result.content,
                {
                    'Message': f'Not a json content - {e}',
                    'Type': 'error',
                },
            )

    def test_validate_no_module(self):
        result = v.validate(
            self.factory.post('/yangvalidator/v2/validate', {'test': 'test'}, content_type='application/json'),
        )

        self.assertEqual(result.status_code, 400)
        self.assertJSONEqual(
            result.content,
            {
                'Message': 'No module received for validation',
                'Type': 'error',
            },
        )

    def test_validate_no_user_or_repo_modules(self):
        result = v.validate(
            self.factory.post(
                '/yangvalidator/v2/validate',
                {'modules-to-validate': {'test': 'test'}},
                content_type='application/json',
            ),
        )

        self.assertEqual(result.status_code, 400)
        self.assertJSONEqual(
            result.content,
            {
                'Message': 'No module received for validation',
                'Type': 'error',
            },
        )

    @mock.patch('yangvalidator.v2.views.os.mkdir', mock.MagicMock(side_effect=Exception('test')))
    def test_validate_error(self):
        validate_json = self.payloads_data['validate_json']
        result = v.validate(
            self.factory.post('/yangvalidator/v2/validate', validate_json, content_type='application/json'),
        )

        self.assertEqual(result.status_code, 200)
        self.assertJSONEqual(result.content, {'output': {'error': 'Failed to parse a document - test'}})

    @mock.patch('yangvalidator.v2.views.extract_files')
    @mock.patch('yangvalidator.v2.views.fnmatch.filter', mock.MagicMock(return_value=['test.txt']))
    @mock.patch('yangvalidator.v2.views.os.listdir', mock.MagicMock())
    def test_validate_doc_cached_draft(self, mock_extract_files: mock.MagicMock):
        mock_extract_files.return_value = 'test'
        request = self.factory.post('/yangvalidator/v2/draft', {'draft': 'test.txt'}, content_type='application/json')
        result = v.validate_doc(request)

        self.assertEqual(result, 'test')
        mock_extract_files.assert_called_with(request, 'test/my-id-archive-mirror/test.txt', True, mock.ANY)

    @mock.patch('yangvalidator.v2.views.extract_files')
    @mock.patch('yangvalidator.v2.views.fnmatch.filter', mock.MagicMock(return_value=[]))
    @mock.patch('yangvalidator.v2.views.os.listdir', mock.MagicMock())
    def test_validate_doc_uncached_draft(self, mock_extract_files: mock.MagicMock):
        mock_extract_files.return_value = 'test'
        request = self.factory.post('/yangvalidator/v2/draft', {'draft': 'test.txt'}, content_type='application/json')
        result = v.validate_doc(request)

        self.assertEqual(result, 'test')
        mock_extract_files.assert_called_with(request, 'https://tools.ietf.org/id/test.txt', True, mock.ANY)

    @mock.patch('yangvalidator.v2.views.extract_files')
    @mock.patch('yangvalidator.v2.views.os.path.exists', mock.MagicMock(side_effect=[True, False]))
    def test_validate_doc_cached_rfc(self, mock_extract_files: mock.MagicMock):
        mock_extract_files.return_value = 'test'
        request = self.factory.post('/yangvalidator/v2/rfc', {'rfc': '1'}, content_type='application/json')
        result = v.validate_doc(request)

        self.assertEqual(result, 'test')
        mock_extract_files.assert_called_with(request, 'test/rfc/rfc1.txt', True, mock.ANY)

    @mock.patch('yangvalidator.v2.views.extract_files')
    @mock.patch('yangvalidator.v2.views.os.path.exists', mock.MagicMock(return_value=False))
    def test_validate_doc_uncached_rfc(self, mock_extract_files: mock.MagicMock):
        mock_extract_files.return_value = 'test'
        request = self.factory.post('/yangvalidator/v2/rfc', {'rfc': '1'}, content_type='application/json')
        result = v.validate_doc(request)

        self.assertEqual(result, 'test')
        mock_extract_files.assert_called_with(request, 'https://tools.ietf.org/rfc/rfc1.txt', True, mock.ANY)

    @mock.patch('yangvalidator.v2.views.os.path.exists', mock.MagicMock(return_value=False))
    def test_validate_doc_missing_rfc(self):
        request = self.factory.post('/yangvalidator/v2/rfc', {}, content_type='application/json')
        result = v.validate_doc(request)

        response = json.loads(result.content)
        self.assertEqual(result.headers['Content-Type'], 'application/json')
        self.assertEqual(result.status_code, 400)
        self.assertIn('Message', response)
        self.assertIn('Type', response)
        self.assertEqual(response.get('Message'), 'Required property "rfc" is missing or empty')
        self.assertEqual(response.get('Type'), 'error')

    @mock.patch('yangvalidator.v2.views.os.path.exists', mock.MagicMock(return_value=False))
    def test_validate_doc_missing_draft(self):
        request = self.factory.post('/yangvalidator/v2/draft', {}, content_type='application/json')
        result = v.validate_doc(request)

        response = json.loads(result.content)
        self.assertEqual(result.headers['Content-Type'], 'application/json')
        self.assertEqual(result.status_code, 400)
        self.assertIn('Message', response)
        self.assertIn('Type', response)
        self.assertEqual(response.get('Message'), 'Required property "draft" is missing or empty')
        self.assertEqual(response.get('Type'), 'error')

    @mock.patch('yangvalidator.v2.views.ModelsChecker')
    @mock.patch('yangvalidator.v2.views.check_missing_amount_one_only', mock.MagicMock(return_value=False))
    def test_create_output_missing(self, mock_checker: mock.MagicMock):
        json_body = deepcopy(self.payloads_data['create_output'])
        json_body['dependencies'] = {'missing': ['missing']}
        json_body['xym'] = {'test': 'test'}
        mock_checker = mock.MagicMock
        mock_checker.find_missing = lambda self: ['missing']
        result = v.create_output(None, 'yang models', 'url', False, 'working dir', ['extracted'], {'test': 'test'})

        self.assertEqual(result.status_code, 202)
        self.assertJSONEqual(result.content, {'output': json_body})

    def test_check_missing_amount_one_only(self):
        self.assertTrue(v.check_missing_amount_one_only({'test': ['test']}))
        self.assertFalse(v.check_missing_amount_one_only({'test': ['test'], 'multiple': ['test', 'more']}))
