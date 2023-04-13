class SailthruErrors(object):
    SHORT_MESSAGE_ERROR_MSG = "Unable to get short message. Unknown error code: {}."
    LONG_MESSAGE_ERROR_MSG = "Unable to get long message. Unknown error code: {}."

    UNSUPPORTED_HTTPS_METHOD = 1
    MISSING_HTTPS_GET_POST_PARAMETER = 2
    INVALID_API_KEY = 3
    DISALLOWED_IP = 4
    AUTHENTICATION_FAILED = 5
    INVALID_UTF_8_CHARACTERS_FOR_FIELD = 6
    INTERNAL_ERROR = 9
    INVALID_EMAIL = 11
    UNKNOWN_SEND_ID = 12
    UNKNOWN_BLAST_ID = 13
    UNKNOWN_TEMPLATE = 14
    UNKNOWN_LIST = 15
    UNKNOWN_SITE = 16
    LOGIN_FAILURE = 17
    INVALID_TIME = 18
    YOU_MUST_BE_APPROVED_TO_EMAIL = 21
    YOU_MUST_BE_A_PREMIUM_CLIENT_TO_USE_THIS_API_CALL = 22
    EMAIL_IS_ON_THE_BLACKLIST = 31
    EMAIL_HAS_OPTED_OUT_OF_DELIVERY_FROM_CLIENT = 32
    EMAIL_HAS_OPTED_OUT_OF_DELIVERY_FROM_TEMPLATE = 33
    EMAIL_MAY_NOT_BE_EMAILED = 34
    EMAIL_IS_A_KNOWN_HARDBOUNCE = 35
    UNVERIFIED_FROM_EMAIL = 36
    EMAIL_WILL_ONLY_ACCEPT_BASIC_TEMPLATES = 37
    UNABLE_TO_DELETE_ALREADY_SENT = 41
    INVALID_UTF_8_CHARACTERS_FOR_FIELD_FIELD_NAME = 42
    OTHER_ERROR = 99
    UNABLE_TO_STREAM = 'XX'

    MESSAGES = {
        UNSUPPORTED_HTTPS_METHOD: {
            "short-msg": "Unsupported HTTPS method",
            "long-msg": "The API only supports GET, POST or DELETE, and some calls only support one or the other. This means you are trying to access an API call with an HTTP method you can't use.",
        },
        MISSING_HTTPS_GET_POST_PARAMETER: {
            "short-msg": "Missing HTTPS GET/POST parameter",
            "long-msg": "You failed to pass a parameter that was required for this API call.",
        },
        INVALID_API_KEY: {
            "short-msg": "Invalid API key",
            "long-msg": "You used the wrong api_key parameter. Check that your client code is using the right API key (obtained in the Settings page).",
        },
        DISALLOWED_IP: {
            "short-msg": "Disallowed IP",
            "long-msg": "You are coming from an IP address that is not allowed according to your settings. You can add the IP to the list on your Settings page.",
        },
        AUTHENTICATION_FAILED: {
            "short-msg": "Authentication failed",
            "long-msg": "The sig parameter you passed was not a correct signature hash of your shared secret and the sorted alphabetical list of the other parameters. For more details on this, see API Details.",
        },
        INVALID_UTF_8_CHARACTERS_FOR_FIELD: {
            "short-msg": "Invalid UTF-8 characters for field",
            "long-msg": "You are passing invalid UTF-8 character as a parameter value.",
        },
        INTERNAL_ERROR: {
            "short-msg": "Internal Error",
            "long-msg": "Something's gone wrong on our end. Your request was probably not saved - try waiting a moment and trying again.",
        },
        INVALID_EMAIL: {
            "short-msg": "Invalid Email",
            "long-msg": "You tried to send to or access an invalid email address.",
        },
        UNKNOWN_SEND_ID: {
            "short-msg": "Unknown send_id",
            "long-msg": "You tried to access a send_id that doesn't exist or doesn't belong to you.",
        },
        UNKNOWN_BLAST_ID: {
            "short-msg": "Unknown blast_id",
            "long-msg": "You tried to access a blast_id that doesn't exist or doesn't belong to you.",
        },
        UNKNOWN_TEMPLATE: {
            "short-msg": "Unknown template",
            "long-msg": "You tried to use a template that doesn't exist. Double-check the name.",
        },
        UNKNOWN_LIST: {
            "short-msg": "Unknown list",
            "long-msg": "You tried to use a list that doesn't exist. Double-check the name.",
        },
        UNKNOWN_SITE: {
            "short-msg": "Unknown site",
            "long-msg": "You tried to import contacts from a site that we don't support.",
        },
        LOGIN_FAILURE: {
            "short-msg": "Login failure",
            "long-msg": "You tried to import contacts, but we couldn't access them - probably either the username or the password was wrong.",
        },
        INVALID_TIME: {
            "short-msg": "Invalid time",
            "long-msg": "You specified a time that didn't make any sense to us. We are very liberal with accepted time formats (anything that PHP's strtotime function can parse), but we recommend a standard format that includes timezone such as RFC 2822 (e.g. Sun, 22 Nov 2012 22:50:27 -0500).",
        },
        YOU_MUST_BE_APPROVED_TO_EMAIL: {
            "short-msg": "You must be approved to email",
            "long-msg": "Your account is not yet approved - until you are approved, you can only send emails to yourself. To get approval contact Support.",
        },
        YOU_MUST_BE_A_PREMIUM_CLIENT_TO_USE_THIS_API_CALL: {
            "short-msg": "You must be a Premium client to use this API call",
            "long-msg": "A few features of the API are only available to paid customers. To set up a paying account, contact Sales.",
        },
        EMAIL_IS_ON_THE_BLACKLIST: {
            "short-msg": "Email is on the blacklist",
            "long-msg": "The email is on your site's permanent blacklist and should never be emailed.",
        },
        EMAIL_HAS_OPTED_OUT_OF_DELIVERY_FROM_CLIENT: {
            "short-msg": "Email has opted out of delivery from client",
            "long-msg": "This email has opted out of delivery from any emails coming from your site and should not be emailed.",
        },
        EMAIL_HAS_OPTED_OUT_OF_DELIVERY_FROM_TEMPLATE: {
            "short-msg": "Email has opted out of delivery from template",
            "long-msg": "This email has opted out of delivery from the specific template you are sending, and should not be sent this type of email.",
        },
        EMAIL_MAY_NOT_BE_EMAILED: {
            "short-msg": "Email may not be emailed",
            "long-msg": "This email has been identified as an email that should never be emailed.",
        },
        EMAIL_IS_A_KNOWN_HARDBOUNCE: {
            "short-msg": "Email is a known hardbounce",
            "long-msg": "This email has been previously identified as a hardbounce, so should not be emailed.",
        },
        UNVERIFIED_FROM_EMAIL: {
            "short-msg": "Unverified from email",
            "long-msg": "You attempted to set the From email to an email address you have not yet verified. You can verify additional From emails in MySailthru.",
        },
        EMAIL_WILL_ONLY_ACCEPT_BASIC_TEMPLATES: {
            "short-msg": "Email will only accept basic templates",
            "long-msg": "The user has opted out of delivery from all templates except basic templates.",
        },
        UNABLE_TO_DELETE_ALREADY_SENT: {
            "short-msg": "Unable to delete, already sent",
            "long-msg": "You attempted to cancel an email that was already sent. It's too late to cancel after it's been sent.",
        },
        INVALID_UTF_8_CHARACTERS_FOR_FIELD_FIELD_NAME: {
            "short-msg": "Invalid UTF-8 characters for field: [field name]",
            "long-msg": "You attempted to upload data in a character set that is not UTF-8 compatible, and therefore won't display properly in a message.",
        },
        OTHER_ERROR: {
            "short-msg": "Other error",
            "long-msg": "Miscellaneous catchall for other errors that have not been assigned codes",
        },
        UNABLE_TO_STREAM: {
            "short-msg": "Unable To Stream",
            "long-msg": "API requests and responses in ISO-8859-1, not UTF-8",
        },
    }

    @classmethod
    def get_short_message(cls, error_code):
        try:
            return cls.MESSAGES[error_code]['short-msg']
        except KeyError:
            return cls.SHORT_MESSAGE_ERROR_MSG.format(error_code)

    @classmethod
    def get_long_message(cls, error_code):
        try:
            return cls.MESSAGES[error_code]['long-msg']
        except KeyError:
            return cls.LONG_MESSAGE_ERROR_MSG.format(error_code)

    @classmethod
    def get_error_data(cls, sailthru_response):
        error = sailthru_response.get_error()
        error_code = error.get_error_code()
        error_message = error.get_message()

        error_short_description = cls.get_short_message(error_code)
        error_long_description = cls.get_long_message(error_code)
        error_full_description = error_short_description + ": " + error_long_description

        data = {
            'code': error_code,
            'message': error_message,
            'description': error_full_description,
            'response status': sailthru_response.get_status_code(),
        }
        return data
