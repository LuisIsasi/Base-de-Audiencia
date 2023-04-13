from .errors import ConversionError


class EmailChangeAudienceUserToSailthru(object):

    def __init__(self, old_user, new_user):
        self.old_user = old_user
        self.new_user = new_user

    def convert(self):
        if not self.new_user.email or not self.old_user.email:
            raise ConversionError("Email is required for conversion")

        data = {
            'id': self.old_user.email,
            'key': 'email',
            'keys': {
                'email': self.new_user.email,
            },
            'fields': {
                'keys': 1,
                'optout_email': 1,
            },
        }

        return data
