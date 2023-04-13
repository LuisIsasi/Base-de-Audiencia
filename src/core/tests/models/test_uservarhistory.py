from django.test import TestCase
from model_mommy import mommy


class UserVarHistoryTestCase(TestCase):

    def test_vars_history_creation(self):
        au = mommy.make('core.Audienceuser')
        au.validate_and_save()

        history = au.vars_history.all()
        self.assertEqual(len(history), 1)

        au.validate_and_save()
        history = au.vars_history.all()
        self.assertEqual(len(history), 1)

        au.vars = {'test': 'value'}
        au.validate_and_save()

        history = au.vars_history.all()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].vars, au.vars)
        self.assertEqual(history[1].vars, {})
