import json
import os
from unittest import mock

from django.http import JsonResponse, HttpResponse
from django.test import SimpleTestCase, RequestFactory

import yangvalidator.v2.views as v

class TestViews(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.resource_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')
        parsers = ['Confd', 'Pyang', 'YangdumpPro', 'Yanglint']
        for parser in parsers:
            patcher = mock.patch('yangvalidator.v2.views.{}Parser'.format(parser), mock.MagicMock)
            mock_parser = patcher.start()
            self.addCleanup(patcher.stop)
            mock_parser.parse_module = lambda self: 'test'

    def test_validate(self):
        validate_json = self.load_payload('validate_json')
        del validate_json['dependencies']
        result = v.validate(
            self.factory.post('/yangvalidator/v2/validate', validate_json, content_type='application/json'), 'test')

        self.assertEqual(result.status_code, 200)
        parsers = ['confd', 'pyang', 'yangdump-pro', 'yanglint']
        self.assertJSONEqual(result.content, {'output': {'yang-catalog@2018-04-03.yang': {parser: 'test' for parser in parsers},
                                                         'xym': 'test'}})

    def test_validate_skip(self):
        validate_json = self.load_payload('validate_json')
        result = v.validate(
            self.factory.post('/yangvalidator/v2/validate', validate_json, content_type='application/json'))

        self.assertEqual(result.status_code, 200)
        warning = 'Following modules yang-catalog@2018-04-03.yang were skipped from validation because you chose' \
                  ' different repo modules as a dependency with same name'
        self.assertJSONEqual(result.content, {'output': {'warning': warning}})

    def test_validate_invalid_method(self):
        result = v.validate(self.factory.get('/yangvalidator/v2/validate'))

        self.assertEqual(result.status_code, 405)
        self.assertJSONEqual(result.content, {'Error': 'Only POST request allowed but GET found'})

    def test_validate_not_json(self):
        result = v.validate(self.factory.post('/yangvalidator/v2/validate'))

        self.assertEqual(result.status_code, 400)
        try:
            json.loads('not json')
        except ValueError as e:
            self.assertJSONEqual(result.content, {'Error': 'Not a json content - {}'.format(e)})

    def test_validate_no_module(self):
        result = v.validate(
            self.factory.post('/yangvalidator/v2/validate', {'test': 'test'}, content_type='application/json'))

        self.assertEqual(result.status_code, 400)
        self.assertJSONEqual(result.content, {'Error': 'No module received for validation'})

    def test_validate_no_user_or_repo_modules(self):
        result = v.validate(mock.MagicMock(method='POST', body=json.dumps({'modules-to-validate': {'test': 'test'}})))
        result = v.validate(
            self.factory.post('/yangvalidator/v2/validate',
                              {'modules-to-validate': {'test': 'test'}},
                              content_type='application/json'))

        self.assertEqual(result.status_code, 400)
        self.assertJSONEqual(result.content, {'Error': 'No module received for validation'})

    @mock.patch('yangvalidator.v2.views.os.mkdir', mock.MagicMock(side_effect=Exception('test')))
    def test_validate_error(self):
        validate_json = self.load_payload('validate_json')
        result = v.validate(
            self.factory.post('/yangvalidator/v2/validate', validate_json, content_type='application/json'))

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

    @mock.patch('yangvalidator.v2.views.json.dump')
    def test_upload_setup(self, mock_dump: mock.MagicMock):
        result = self.client.post('/yangvalidator/v2/upload-files-setup',
                                  {'latest': True, 'get-from-options': True},
                                  'application/json')

        self.assertEqual(mock_dump.call_args[0][0], {'latest': True, 'get-from-options': True})
        self.assertEqual(result.headers['Content-Type'], 'application/json')
        self.assertEqual(result.status_code, 200)
        self.assertIn('cache', json.loads(result.content).get('output'))

    @mock.patch('yangvalidator.v2.views.json.dump')
    def test_upload_setup_defaults(self, mock_dump: mock.MagicMock):
        result = self.client.post('/yangvalidator/v2/upload-files-setup',
                                  content_type='application/json')

        self.assertEqual(mock_dump.call_args[0][0], {'latest': False, 'get-from-options': False})
        self.assertEqual(result.headers['Content-Type'], 'application/json')
        self.assertEqual(result.status_code, 200)
        self.assertIn('cache', json.loads(result.content).get('output'))

    @mock.patch('yangvalidator.v2.views.upload_draft_id')
    def test_upload_draft(self, mock_upload_draft_id: mock.MagicMock):
        v.upload_draft(self.factory.post('/yangvalidator/v2/draft-validator'))
        self.assertEqual(mock_upload_draft_id.call_args[0][1], None)

    @mock.patch('yangvalidator.v2.views.os.path.exists', mock.MagicMock(return_value=True))
    @mock.patch('yangvalidator.v2.views.open', mock.mock_open(read_data=json.dumps({'test': 'test'})))
    def test_load_pre_setup(self):
        result = v.load_pre_setup('working dir', 1)

        self.assertEqual(result, {'test': 'test'})

    @mock.patch('yangvalidator.v2.views.os.path.exists', mock.MagicMock(return_value=False))
    @mock.patch('yangvalidator.v2.views.open', mock.mock_open(read_data=json.dumps({'test': 'test'})))
    def test_load_pre_setup_not_found(self):
        result = v.load_pre_setup('working dir', 1)

        self.assertEqual(result.status_code, 400)
        self.assertJSONEqual(result.content, {'Error': 'Cache file with id - {} does not exist.'
                                              ' Please use pre setup first. Post request on path'
                                              ' /yangvalidator/v2/upload-files-setup where you provide'
                                              ' "latest" and "get-from-options" key with true or false'
                                              ' variable'.format(1)})

    @mock.patch('yangvalidator.v2.views.extract_files')
    @mock.patch('yangvalidator.v2.views.load_pre_setup', mock.MagicMock(return_value={'latest': True}))
    def test_upload_draft_id(self, mock_extract_files: mock.MagicMock):
        mock_extract_files.return_value = JsonResponse({'test': 'test'})
        with open('tests/resources/all_modules/yang-catalog@2018-04-03.yang') as f:
            request = self.factory.post('/yangvalidator/v2/draft-validator/1', {'name': 'yang-catalog@2018-04-03.yang',
                                                                                'data': f})
            result = v.upload_draft_id(request, 1)
        
        self.assertEqual(result.status_code, 200)
        self.assertJSONEqual(result.content, [{'test': 'test', 'document-name': 'yang-catalog@2018-04-03.yang'}])
        mock_extract_files.assert_called_with(request, mock.ANY, True, mock.ANY, remove_working_dir=False)

    
    def test_upload_draft_id_not_set_up(self):
        result = self.client.post('/yangvalidator/v2/draft-validator/1')

        self.assertEqual(result.headers['Content-Type'], 'application/json')
        self.assertEqual(result.status_code, 400)
        self.assertJSONEqual(result.content, {'Error': 'Cache file with id - {} does not exist.'
                                              ' Please use pre setup first. Post request on path'
                                              ' /yangvalidator/v2/upload-files-setup where you provide'
                                              ' "latest" and "get-from-options" key with true or false'
                                              ' variable'.format(1)})

    @mock.patch('yangvalidator.v2.views.load_pre_setup', mock.MagicMock(return_value={'latest': True}))
    @mock.patch('yangvalidator.v2.views.os.mkdir', mock.MagicMock(side_effect=Exception('test')))
    def test_upload_draft_id_exception(self):
        with open('tests/resources/all_modules/yang-catalog@2018-04-03.yang') as f:
            result = self.client.post('/yangvalidator/v2/draft-validator/1', {'name': 'yang-catalog@2018-04-03.yang',
                                                                              'data': f})
        
        self.assertEqual(result.status_code, 400)
        self.assertJSONEqual(result.content, {'Error': 'Failed to upload and validate documents - test'})

    @mock.patch('yangvalidator.v2.views.create_output')
    @mock.patch('yangvalidator.v2.views.open')
    @mock.patch('yangvalidator.v2.views.load_pre_setup', mock.MagicMock(return_value={'latest': True,
                                                                                      'get-from-options': True}))
    def test_upload_file(self, mock_open: mock.MagicMock, mock_create_output: mock.MagicMock):
        mock.mock_open(mock_open)
        mock_create_output.return_value = 'test'
        with open('tests/resources/all_modules/yang-catalog@2018-04-03.yang') as f:
            request = self.factory.post('/yangvalidator/v2/validator/1', {'name': 'yang-catalog@2018-04-03.yang',
                                                                          'data': f})
            result = v.upload_file(request, 1)

        self.assertEqual(result, 'test')
        mock_create_output.assert_called_with(request, 'tests/resources/all_modules', None, True,
                                              'tests/resources/tmp/yangvalidator/1', ['yang-catalog@2018-04-03.yang'],
                                              choose_options=True)

    @mock.patch('yangvalidator.v2.views.ZipFile')
    @mock.patch('yangvalidator.v2.views.create_output')
    @mock.patch('yangvalidator.v2.views.open')
    @mock.patch('yangvalidator.v2.views.load_pre_setup', mock.MagicMock(return_value={'latest': True,
                                                                                      'get-from-options': True}))
    def test_upload_file_zip(self, mock_open: mock.MagicMock,
                             mock_create_output: mock.MagicMock, mock_zip: mock.MagicMock):
        mock.mock_open(mock_open)
        mock_create_output.return_value = 'test'
        mock_zip = mock.MagicMock
        mock_zip.extract_all = lambda self: None
        mock_zip.namelist = lambda self: ['yang-catalog@2018-04-03.yang']
        with mock_open('tests/resources/all_modules/yang-catalog@2018-04-03.zip') as f:
            f.name = 'yang-catalog@2018-04-03.zip'
            request = self.factory.post('/yangvalidator/v2/validator/1', {'name': 'yang-catalog@2018-04-03.zip',
                                                                          'data': f})
            result = v.upload_file(request, 1)

        self.assertEqual(result, 'test')
        mock_create_output.assert_called_with(request, 'tests/resources/all_modules', None, True,
                                              'tests/resources/tmp/yangvalidator/1', ['yang-catalog@2018-04-03.yang'],
                                              choose_options=True)

    def test_upload_file_not_set_up(self):
        result = self.client.post('/yangvalidator/v2/validator/1')

        self.assertEqual(result.status_code, 400)
        self.assertJSONEqual(result.content, {'Error': 'Cache file with id - {} does not exist.'
                                              ' Please use pre setup first. Post request on path'
                                              ' /yangvalidator/v2/upload-files-setup where you provide'
                                              ' "latest" and "get-from-options" key with true or false'
                                              ' variable'.format(1)})

    @mock.patch('yangvalidator.v2.views.load_pre_setup', mock.MagicMock(return_value={'latest': True}))
    @mock.patch('yangvalidator.v2.views.os.open', mock.MagicMock(side_effect=Exception()))
    def test_upload_file_exception(self):
        with open('tests/resources/all_modules/yang-catalog@2018-04-03.yang') as f:
            result = self.client.post('/yangvalidator/v2/validator/1', {'name': 'yang-catalog@2018-04-03.yang',
                                                                        'data': f})
        
        self.assertEqual(result.status_code, 400)
        self.assertJSONEqual(result.content, {'Error': 'Failed to get yang files'})

    @mock.patch('yangvalidator.v2.views.create_output')
    @mock.patch('yangvalidator.v2.views.XymParser')
    def test_extract_files(self, mock_parser: mock.MagicMock, mock_create_output: mock.MagicMock):
        mock_parser = mock.MagicMock
        mock_parser.parse_and_extract = lambda self: ('extracted', 'xym response')
        v.extract_files(None, 'url', True, 'working dir', True)

        mock_create_output.assert_called_with(None, 'tests/resources/all_modules', 'url', True, 'working dir', 'extracted',
                                              'xym response', remove_working_dir=True)

    @mock.patch('yangvalidator.v2.views.ModelsChecker', mock.MagicMock())
    @mock.patch('yangvalidator.v2.views.check_missing_amount_one_only', mock.MagicMock(return_value=True))
    def test_create_output_failed_to_load(self):
        result = v.create_output(None, 'yang models', 'url', False, 'working dir', [])

        self.assertEqual(result.status_code, 400)
        self.assertJSONEqual(result.content, {'Error': 'Failed to load any yang modules. Please provide at least one'
                                                       ' yang module. File must have .yang extension'})

    @mock.patch('yangvalidator.v2.views.ModelsChecker', mock.MagicMock())
    @mock.patch('yangvalidator.v2.views.check_missing_amount_one_only', mock.MagicMock(return_value=True))
    def test_create_output_failed_to_parse(self):
        result = v.create_output(None, 'yang models', 'url', False, 'working dir', [], {'stderr': 'error'})

        self.assertEqual(result.status_code, 200)
        self.assertJSONEqual(result.content, {'Error': 'Failed to xym parse url url',
                                              'xym': {'stderr': 'error'}})

    @mock.patch('yangvalidator.v2.views.ModelsChecker', mock.MagicMock())
    @mock.patch('yangvalidator.v2.views.check_missing_amount_one_only', mock.MagicMock(return_value=True))
    def test_create_output_not_found(self):
        result = v.create_output(None, 'yang models', 'url', False, 'working dir', [], {'test': 'test'})

        self.assertEqual(result.status_code, 200)
        self.assertJSONEqual(result.content, {'Error': 'No modules found using xym in url url',
                                              'xym': {'test': 'test'}})

    @mock.patch('yangvalidator.v2.views.ModelsChecker')
    @mock.patch('yangvalidator.v2.views.validate')
    @mock.patch('yangvalidator.v2.views.check_missing_amount_one_only', mock.MagicMock(return_value=True))
    def test_create_output_choose_options_and_none_missing(self, mock_validate: mock.MagicMock,
                                                           mock_checker: mock.MagicMock,):
        json_body = self.load_payload('create_output')
        json_body['dependencies'] = {'missing': [], 'existing': {}}
        mock_validate.return_value='test'
        mock_checker = mock.MagicMock
        mock_checker.find_missing = lambda self: []
        mock_checker.get_existing_dependencies = lambda self: ({}, False)
        result = v.create_output(None, 'yang models', 'url', False, 'working dir', ['extracted'], choose_options=True)

        self.assertEqual(result, 'test')
        mock_validate.assert_called_with(None, None, json_body)
    
    @mock.patch('yangvalidator.v2.views.ModelsChecker')
    @mock.patch('yangvalidator.v2.views.check_missing_amount_one_only', mock.MagicMock(return_value=True))
    def test_create_output_choose_options_and_missing(self, mock_checker: mock.MagicMock):
        json_body = self.load_payload('create_output')
        json_body['dependencies'] = {'missing': ['missing'], 'existing': {}}
        mock_checker = mock.MagicMock
        mock_checker.find_missing = lambda self: ['missing']
        mock_checker.get_existing_dependencies = lambda self: ({}, False)
        result = v.create_output(None, 'yang models', 'url', False, 'working dir', ['extracted'], choose_options=True)

        self.assertEqual(result.status_code, 202)
        self.assertJSONEqual(result.content, {'output': json_body})

    @mock.patch('yangvalidator.v2.views.ModelsChecker')
    @mock.patch('yangvalidator.v2.views.validate')
    @mock.patch('yangvalidator.v2.views.check_missing_amount_one_only', mock.MagicMock(return_value=True))
    def test_create_output_latest(self, mock_validate: mock.MagicMock, mock_checker: mock.MagicMock):
        json_body = self.load_payload('create_output')
        json_body['dependencies'] = {'repo-modules': []}
        mock_validate.return_value = 'test'
        mock_checker = mock.MagicMock
        mock_checker.find_missing = lambda self: ['missing']
        mock_checker.get_latest_revision = lambda self: []
        result = v.create_output(None, 'yang models', 'url', True, 'working dir', ['extracted'])

        self.assertEqual(result, 'test')
        mock_validate.assert_called_with(None, None, json_body)

    @mock.patch('yangvalidator.v2.views.ModelsChecker')
    @mock.patch('yangvalidator.v2.views.validate')
    @mock.patch('yangvalidator.v2.views.check_missing_amount_one_only', mock.MagicMock(return_value=False))
    def test_create_output_none_missing(self, mock_validate: mock.MagicMock, mock_checker: mock.MagicMock):
        json_body = self.load_payload('create_output')
        mock_validate.return_value = 'test'
        mock_checker = mock.MagicMock
        mock_checker.find_missing = lambda self: []
        result = v.create_output(None, 'yang models', 'url', False, 'working dir', ['extracted'])

        self.assertEqual(result, 'test')
        mock_validate.assert_called_with(None, None, json_body)

    @mock.patch('yangvalidator.v2.views.ModelsChecker')
    @mock.patch('yangvalidator.v2.views.check_missing_amount_one_only', mock.MagicMock(return_value=False))
    def test_create_output_missing(self, mock_checker: mock.MagicMock):
        json_body = self.load_payload('create_output')
        json_body['dependencies'] = {'missing': ['missing']}
        json_body['xym'] = {'test': 'test'}
        mock_checker = mock.MagicMock
        mock_checker.find_missing = lambda self: ['missing']
        result = v.create_output(None, 'yang models', 'url', False, 'working dir', ['extracted'], {'test': 'test'})

        self.assertEqual(result.status_code, 202)
        self.assertJSONEqual(result.content, {'output': json_body})


    def test_check_missing_amount_one_only(self):
        self.assertTrue(v.check_missing_amount_one_only({'test': ['test']}))
        self.assertFalse(v.check_missing_amount_one_only({
            'test': ['test'],
            'multiple': ['test', 'more']
        }))

    def load_payload(self, key: str) -> dict:
        with open(os.path.join(self.resource_path, 'payloads.json')) as f:
            return json.load(f)[key]
