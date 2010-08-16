# (c) 2010 by Anton Korenyushkin

from django.test import TestCase


class Test(TestCase):
    def test_addition(self):
        self.assertEqual(2 + 2, 4)
