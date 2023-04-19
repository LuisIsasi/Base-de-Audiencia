from django.test import TestCase

from ..errors import SailthruErrors


class SailthruErrorsTestCase(TestCase):
    def test_message(self):
        st_errors = SailthruErrors()
        error_codes = [0, None]  # values that aren't a valid error code
        for error_code in error_codes:
            msg = st_errors.get_short_message(error_code)
            self.assertEqual(st_errors.SHORT_MESSAGE_ERROR_MSG.format(error_code), msg)

            msg = st_errors.get_long_message(error_code)
            self.assertIn(st_errors.LONG_MESSAGE_ERROR_MSG.format(error_code), msg)

        valid_codes = [
            st_errors.UNSUPPORTED_HTTPS_METHOD,
            st_errors.MISSING_HTTPS_GET_POST_PARAMETER,
            st_errors.INVALID_API_KEY,
            st_errors.DISALLOWED_IP,
            st_errors.AUTHENTICATION_FAILED,
            st_errors.INVALID_UTF_8_CHARACTERS_FOR_FIELD,
            st_errors.INTERNAL_ERROR,
            st_errors.INVALID_EMAIL,
            st_errors.UNKNOWN_SEND_ID,
            st_errors.UNKNOWN_BLAST_ID,
            st_errors.UNKNOWN_TEMPLATE,
            st_errors.UNKNOWN_LIST,
            st_errors.UNKNOWN_SITE,
            st_errors.LOGIN_FAILURE,
            st_errors.INVALID_TIME,
            st_errors.YOU_MUST_BE_APPROVED_TO_EMAIL,
            st_errors.YOU_MUST_BE_A_PREMIUM_CLIENT_TO_USE_THIS_API_CALL,
            st_errors.EMAIL_IS_ON_THE_BLACKLIST,
            st_errors.EMAIL_HAS_OPTED_OUT_OF_DELIVERY_FROM_CLIENT,
            st_errors.EMAIL_HAS_OPTED_OUT_OF_DELIVERY_FROM_TEMPLATE,
            st_errors.EMAIL_MAY_NOT_BE_EMAILED,
            st_errors.EMAIL_IS_A_KNOWN_HARDBOUNCE,
            st_errors.UNVERIFIED_FROM_EMAIL,
            st_errors.EMAIL_WILL_ONLY_ACCEPT_BASIC_TEMPLATES,
            st_errors.UNABLE_TO_DELETE_ALREADY_SENT,
            st_errors.INVALID_UTF_8_CHARACTERS_FOR_FIELD_FIELD_NAME,
            st_errors.OTHER_ERROR,
            st_errors.UNABLE_TO_STREAM,
        ]

        for error_code in valid_codes:
            st_errors.get_short_message(error_code)
            st_errors.get_long_message(error_code)
