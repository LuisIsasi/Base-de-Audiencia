from django.test import TestCase
from model_mommy import mommy

from core.models import EmailChangeAudienceUser


class UserTestCase(TestCase):
    def test_qs(self):
        user = mommy.make("core.AudienceUser", email="")
        self.assertEqual(EmailChangeAudienceUser.objects.count(), 0)
        user = mommy.make("core.AudienceUser", email=None)
        self.assertEqual(EmailChangeAudienceUser.objects.count(), 0)

        user = mommy.make("core.AudienceUser", email="a@a.com")
        self.assertEqual(EmailChangeAudienceUser.objects.count(), 1)
