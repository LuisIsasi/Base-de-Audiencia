from model_mommy import mommy
from rest_framework import status
from rest_framework import test as rest_test


class ProductActionViewsetTests(rest_test.APITestCase):

    def setUp(self):
        from django.contrib.auth.models import User
        from rest_framework.authtoken.models import Token
        u = User.objects.create(username='test')
        t = Token.objects.create(user=u)
        self.client.force_authenticate(user=u, token=t)

    def test_subscriptions_list_empty(self):
        au = mommy.make('core.AudienceUser', email="a@a.com")
        au.validate_and_save()

        r = self.client.get(
            "/api/audience-users/{}/subscriptions".format(au.pk), format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json(), [])

    def test_subscriptions_list_with_unknown_user(self):
        r = self.client.get("/api/audience-users/1/subscriptions", format='json')
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_subscription_create_with_bad_user_pk(self):
        list_ = mommy.make(
            'core.List', slug='newsletter_foo', name='newsletter foo', type='newsletter'
        )
        list_.validate_and_save()

        r = self.client.post(
            "/api/audience-users/1/subscriptions",
            {'list': 'newsletter_foo', 'active': True},
            format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {'audience_user': 'Does not exist.'})

    def test_subscription_create_with_bad_list(self):
        au = mommy.make('core.AudienceUser', email="a@a.com")
        au.validate_and_save()

        payload = {'list': 'foo', 'active': True}
        r = self.client.post(
            "/api/audience-users/{}/subscriptions".format(au.pk), payload, format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {'list': 'Does not exist.'})

    def test_subscription_create_with_bad_active_value(self):
        au = mommy.make('core.AudienceUser', email="a@a.com")
        au.validate_and_save()

        list_ = mommy.make(
            'core.List', slug='newsletter_foo', name='newsletter foo', type='newsletter'
        )
        list_.validate_and_save()

        payload = {'list': list_.slug, 'active': 'foo'}
        r = self.client.post(
            "/api/audience-users/{}/subscriptions".format(au.pk), payload, format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {'active': ["'foo' value must be either True or False."]})

    def test_subscription_create_with_active_as_none(self):
        au = mommy.make('core.AudienceUser', email="a@a.com")
        au.validate_and_save()

        list_ = mommy.make(
            'core.List', slug='newsletter_foo', name='newsletter foo', type='newsletter'
        )
        list_.validate_and_save()

        payload = {'list': list_.slug, 'active': None}
        r = self.client.post(
            "/api/audience-users/{}/subscriptions".format(au.pk), payload, format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {'active': 'This field is required.'})

    def test_subscription_create_with_list_as_none(self):
        au = mommy.make('core.AudienceUser', email="a@a.com")
        au.validate_and_save()

        payload = {'list': None, 'active': True}
        r = self.client.post(
            "/api/audience-users/{}/subscriptions".format(au.pk), payload, format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {'list': 'This field is required.'})

    def test_subscription_create_happy_path(self):
        au = mommy.make('core.AudienceUser', email="a@a.com")
        au.validate_and_save()

        list_ = mommy.make(
            'core.List', slug='newsletter_foo', name='newsletter foo', type='newsletter'
        )
        list_.validate_and_save()

        payload = {'list': list_.slug, 'active': False}
        r = self.client.post(
            "/api/audience-users/{}/subscriptions".format(au.pk), payload, format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        r_json = r.json()
        self.assertEqual(r_json['active'], False)
        self.assertEqual(r_json['list']['slug'], payload['list'])
        self.assertEqual(sorted(r_json.keys()), sorted(['active', 'created', 'id', 'list', 'modified']))

    def test_subscription_create_happy_path_with_implicit_sub(self):
        au = mommy.make('core.AudienceUser', email="a@a.com")
        au.validate_and_save()

        list_ = mommy.make(
            'core.List', slug='newsletter_foo', name='newsletter foo', type='newsletter'
        )
        list_.validate_and_save()

        payload = {'list': list_.slug}
        r = self.client.post(
            "/api/audience-users/{}/subscriptions".format(au.pk), payload, format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        r_json = r.json()
        self.assertEqual(r_json['active'], True)
        self.assertEqual(r_json['list']['slug'], payload['list'])

    def test_subscription_sub_then_unsub(self):
        au = mommy.make('core.AudienceUser', email="a@a.com")
        au.validate_and_save()

        list_ = mommy.make(
            'core.List', slug='newsletter_foo', name='newsletter foo', type='newsletter'
        )
        list_.validate_and_save()

        payload = {'list': list_.slug, 'active': True}
        r = self.client.post(
            "/api/audience-users/{}/subscriptions".format(au.pk), payload, format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        r_json = r.json()
        self.assertEqual(r_json['active'], True)

        payload = {'list': list_.slug, 'active': False}
        r = self.client.post(
            "/api/audience-users/{}/subscriptions".format(au.pk), payload, format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        r_json = r.json()
        self.assertEqual(r_json['active'], False)

    def test_subscription_create_with_log_override(self):
        au = mommy.make('core.AudienceUser', email="a@a.com")
        au.validate_and_save()

        list_ = mommy.make(
            'core.List', slug='newsletter_foo', name='newsletter foo', type='newsletter'
        )
        list_.validate_and_save()

        payload = {'list': list_.slug, 'active': True}
        payload['log_override'] = {
            "action": "update",
        }
        r = self.client.post(
            "/api/audience-users/{}/subscriptions".format(au.pk), payload, format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_subscription_create_with_log_override_comment(self):
        au = mommy.make('core.AudienceUser', email="a@a.com")
        au.validate_and_save()

        list_ = mommy.make(
            'core.List', slug='newsletter_foo', name='newsletter foo', type='newsletter'
        )
        list_.validate_and_save()

        payload = {'list': list_.slug, 'active': True}
        payload['log_override'] = {
            "action": "update",
            "comment": "foo"
        }
        r = self.client.post(
            "/api/audience-users/{}/subscriptions".format(au.pk), payload, format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_subscription_create_with_bad_log_override_action(self):
        au = mommy.make('core.AudienceUser', email="a@a.com")
        au.validate_and_save()

        list_ = mommy.make(
            'core.List', slug='newsletter_foo', name='newsletter foo', type='newsletter'
        )
        list_.validate_and_save()

        payload = {'list': list_.slug, 'active': True}
        payload['log_override'] = {
            "action": "foobarbaz",
            "comment": "foo"
        }
        r = self.client.post(
            "/api/audience-users/{}/subscriptions".format(au.pk), payload, format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {'__all__': ['Unknown subscription log override action']})

    def test_subscription_update_with_bad_log_override_action(self):
        au = mommy.make('core.AudienceUser', email="a@a.com")
        au.validate_and_save()

        list_ = mommy.make(
            'core.List', slug='newsletter_foo', name='newsletter foo', type='newsletter'
        )
        list_.validate_and_save()

        payload = {'list': list_.slug, 'active': True}
        r = self.client.post(
            "/api/audience-users/{}/subscriptions".format(au.pk), payload, format='json'
        )

        payload = {'list': list_.slug, 'active': False}
        payload['log_override'] = {
            "action": "foobarbaz",
            "comment": "foo"
        }
        r = self.client.post(
            "/api/audience-users/{}/subscriptions".format(au.pk), payload, format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {'action': ["Value 'foobarbaz' is not a valid choice."]})

    def test_subscription_get_view(self):
        au = mommy.make('core.AudienceUser', email="a@a.com")
        au.validate_and_save()

        list_ = mommy.make(
            'core.List', slug='newsletter_foo', name='newsletter foo', type='newsletter'
        )
        list_.validate_and_save()

        payload = {'list': list_.slug, 'active': False}
        r = self.client.post(
            "/api/audience-users/{}/subscriptions".format(au.pk), payload, format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        created_json = r.json()
        self.assertEqual(created_json['active'], False)
        self.assertEqual(created_json['list']['slug'], payload['list'])
        self.assertEqual(
            sorted(created_json.keys()),
            sorted(['active', 'created', 'id', 'list', 'modified'])
        )

        r = self.client.get(
            "/api/audience-users/{}/subscriptions/{}".format(au.pk, created_json['id']),
            format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()['id'], created_json['id'])
        self.assertEqual(r.json()['list'], created_json['list'])

    def test_subscription_get_view_for_unknown_user(self):
        au = mommy.make('core.AudienceUser', email="a@a.com")
        au.validate_and_save()

        list_ = mommy.make(
            'core.List', slug='newsletter_foo', name='newsletter foo', type='newsletter'
        )
        list_.validate_and_save()

        payload = {'list': list_.slug, 'active': False}
        r = self.client.post(
            "/api/audience-users/{}/subscriptions".format(au.pk), payload, format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        created_json = r.json()
        self.assertEqual(created_json['active'], False)
        self.assertEqual(created_json['list']['slug'], payload['list'])
        self.assertEqual(
            sorted(created_json.keys()),
            sorted(['active', 'created', 'id', 'list', 'modified'])
        )

        assert au.pk != 9999
        r = self.client.get(
            "/api/audience-users/9999/subscriptions/{}".format(created_json['id']),
            format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_subscription_unsupported_http_methods(self):
        au = mommy.make('core.AudienceUser', email="a@a.com")
        au.validate_and_save()

        list_ = mommy.make(
            'core.List', slug='newsletter_foo', name='newsletter foo', type='newsletter'
        )
        list_.validate_and_save()

        payload = {'list': list_.slug, 'active': False}
        r = self.client.post(
            "/api/audience-users/{}/subscriptions".format(au.pk), payload, format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        subscrip_id = r.json()['id']

        for request_method in (self.client.put, self.client.delete, self.client.patch):
            r = request_method(
                "/api/audience-users/{}/subscriptions/{}".format(au.pk, subscrip_id),
                payload,
                format='json'
            )
            self.assertEqual(r.status_code, status.HTTP_501_NOT_IMPLEMENTED)

    def test_subscription_post_on_existing(self):
        au = mommy.make('core.AudienceUser', email="a@a.com")
        au.validate_and_save()

        list_ = mommy.make(
            'core.List', slug='newsletter_foo', name='newsletter foo', type='newsletter'
        )
        list_.validate_and_save()

        payload = {'list': list_.slug, 'active': False}
        r = self.client.post(
            "/api/audience-users/{}/subscriptions".format(au.pk), payload, format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        r = self.client.post(
            "/api/audience-users/{}/subscriptions/{}".format(au.pk, r.json()['id']),
            payload,
            format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)



    # verify subscription log override and comment
    # test subscription triggering
    # list
    # get
    # put, delete, patch == all not implemented
    # empty payload
