class MockedSailthruClient(object):
    class MockedResponse(object):
        def __init__(self):
            self.ok = True
            self.body = None
            self.response_error_code = 99
            self.response_error_message = "Invalid email: a@a.com"

        def is_ok(self):
            return self.ok

        def get_body(self):
            return self.body

        def get_status_code(self):
            return 418

        def get_error(self):
            return type('Foo', (), {
                'get_error_code': lambda: self.response_error_code,
                'get_message': lambda: self.response_error_message,
            })

    def __init__(self):
        self.api_post_return_value = self.MockedResponse()
        self.api_post_raise_exception = False

    def api_post(self, endpoint_name, data):
        if self.api_post_raise_exception:
            raise Exception("Test Exception")
        return self.api_post_return_value
