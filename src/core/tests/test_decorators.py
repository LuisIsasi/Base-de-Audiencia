import logging
from datetime import datetime, timedelta
from unittest import mock

from django import test
from django.core.cache import cache

from .. import decorators


class DecoratorsTestCase(test.TestCase):
    throttle_interval = 60 * 5  # Should be plenty long enough to run our tests
    throttle_task_key = decorators.throttle.task_lock_prefix + 'throttled'
    throttle_queue_key = decorators.throttle.queue_lock_prefix + 'throttled'

    request = type('Foo', (object,), {
        'id': 'just an id',
    })
    name = 'foo'

    @staticmethod
    def retry(*args, **kwargs):
        pass


    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_ran = None

    @decorators.throttle(interval_seconds=throttle_interval, logger_name='')
    def throttled(self):
        self.task_ran = True

    def setUp(self):
        self.task_ran = False

    def tearDown(self):
        cache.clear()

    def test_task_runs(self):
        self.throttled()
        self.assertTrue(self.task_ran)

    @mock.patch('core.decorators.celery_app.send_task')
    def test_task_throttled(self, send_task):
        self.throttled()
        self.assertTrue(self.task_ran)
        self.assertFalse(cache.add(self.throttle_task_key, True, 10000))

        self.task_ran = False
        self.throttled()
        self.assertFalse(self.task_ran)
        self.assertFalse(cache.add(self.throttle_queue_key, True, 10000))

        self.throttled()
        self.assertFalse(self.task_ran)

        self.throttled()
        self.assertFalse(self.task_ran)

    @mock.patch('core.decorators.cache')
    def test_delay_none(self, mocked_cache):
        mocked_cache.add.return_value = False
        mocked_cache.get.return_value = None
        self.throttled()
        name = 0
        arguments = 1
        for called in mocked_cache.mock_calls:
            if called[name] == 'add' and called[arguments][0] == self.throttle_queue_key:
                delay = called[arguments][2]
                self.assertEqual(delay, self.throttle_interval)
                return
        self.fail("Expected calls not found.")

    @mock.patch('core.decorators.cache')
    def test_delay(self, mocked_cache):
        mocked_cache.add.return_value = False
        stored_time = datetime.now() - timedelta(seconds=2 * self.throttle_interval)
        mocked_cache.get.return_value = stored_time.timestamp()
        self.throttled()
        name = 0
        arguments = 1
        for called in mocked_cache.mock_calls:
            if called[name] == 'add' and called[arguments][0] == self.throttle_queue_key:
                delay = called[arguments][2]
                self.assertEqual(delay, 1)
                return
        self.fail("Expected calls not found.")
