from django import test
from django.contrib.admin.sites import AdminSite

from ... import admin as core_admin, models as core_models


@test.override_settings(SAILTHRU_SYNC_SIGNALS_ENABLED=False, RAVEN_CONFIG={'dsn': None})
class EmailChangeAdminTest(test.TestCase):

    def test_get_actions(self):
        a = core_admin.EmailChangeAudienceUserAdmin(core_models.EmailChangeAudienceUser, AdminSite)
        self.assertEqual(a.get_actions(), [])

    def test_has_add_permission(self):
        a = core_admin.EmailChangeAudienceUserAdmin(core_models.EmailChangeAudienceUser, AdminSite)
        self.assertFalse(a.has_add_permission())

    def test_has_delete_permission(self):
        a = core_admin.EmailChangeAudienceUserAdmin(core_models.EmailChangeAudienceUser, AdminSite)
        self.assertFalse(a.has_delete_permission())
