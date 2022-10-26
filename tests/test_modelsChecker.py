from django.test import SimpleTestCase

from yangvalidator.v2.modelsChecker import ModelsChecker


class TestModelsChecker(SimpleTestCase):
    def test_find_missing(self):
        mc = ModelsChecker('', '', [])
        mc._dependencies = {'test': ['test@2000-01-01.yang', 'test@2020-01-01']}
        result = mc.find_missing()

        self.assertEqual(result, {'test': ['2000-01-01', '2020-01-01']})

    def test_find_missing_in_existing(self):
        mc = ModelsChecker('', '', ['test@2010-01-01.yang'])
        mc._dependencies = {'test': ['test@2000-01-01.yang', 'test@2020-01-01']}
        result = mc.find_missing()

        self.assertEqual(result, {})

    def test_get_existing_dependencies(self):
        mc = ModelsChecker('', '', ['test@2010-01-01.yang'])
        mc._dependencies = {'test': ['test@2000-01-01.yang', 'test@2020-01-01']}
        result, found_repo_modules = mc.get_existing_dependencies()

        self.assertEqual(
            result,
            {'test': {'user-dependencies': '2010-01-01', 'repo-dependencies': ['2000-01-01', '2020-01-01']}},
        )
        self.assertEqual(found_repo_modules, True)

    def test_get_existing_dependencies_repo_modules_not_found(self):
        mc = ModelsChecker('', '', ['other@2010-01-01.yang'])
        mc._dependencies = {'test': ['test@2000-01-01.yang', 'test@2020-01-01']}
        result, found_repo_modules = mc.get_existing_dependencies()

        self.assertEqual(result, {})
        self.assertEqual(found_repo_modules, False)

    def test_get_latest_revision(self):
        mc = ModelsChecker('', '', [])
        mc._missing = {'test': ['2000-01-01', '2020-02-29', '2010-3-4']}
        result = mc.get_latest_revision()

        self.assertEqual(result, ['test@2020-02-29.yang'])

    def test_get_latest_revision_exception(self):
        mc = ModelsChecker('', '', [])
        mc._missing = {'test': ['2000-30-01', '2020-02-29', '2010-3-4']}
        with self.assertRaises(ValueError):
            mc.get_latest_revision()
