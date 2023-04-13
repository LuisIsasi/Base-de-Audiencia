from .errors import ConversionError


class AudienceUserToSailthruDelete(object):
    merge_user_email = 'deleted.user@govexec.com'

    def __init__(self, user):
        self.user = user

    def convert(self):
        if self.user.email:
            id_val = self.user.email
            key = 'email'
        elif self.user.sailthru_id:
            id_val = self.user.sailthru_id
            key = 'sid'
        else:
            raise ConversionError("A way to identify the user with Sailthru is required.")

        data = {
            'id': id_val,
            'key': key,
            'keys': {
                'email': self.merge_user_email,
            },
            'fields': {
                'keys': 1,
            },
            'keysconflict': 'merge'
        }

        return data
