from django.test import SimpleTestCase

from yangvalidator.v2.modelsChecker import ModelsChecker


class TestModelsChecker(SimpleTestCase):
    def test_find_missing(self):
        mc = ModelsChecker('', '', [])
        mc._dependencies = {'test': ['test@2000-01-01.yang', 'test@2020-01-01']}
        result = mc.find_missing()

        self.assertEqual(result, {'test': ['2000-01-01', '2020-01-01']})
