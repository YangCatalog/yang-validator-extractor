from django.test import TestCase

import yangvalidator.v2.views as v

class TestViews(TestCase):
    
    def test_check_missing_amount_one_only(self):
        self.assertTrue(v.check_missing_amount_one_only({}))
