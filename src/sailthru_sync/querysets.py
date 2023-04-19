from django.db import models
import sentry_sdk

from .errors import SailthruErrors


class SyncFailureQuerySet(models.QuerySet):

    skip_sentry_errors = (SailthruErrors.INVALID_EMAIL,)

    def should_log_to_sentry(self, sailthru_response):
        error = sailthru_response.get_error()
        if not error:
            return True
        return error.get_error_code() not in self.skip_sentry_errors

    def from_message(self, msg, failed_instance):
        data = {
            "message": msg,
            "failed_instance": failed_instance,
        }

        failure = self.model(**data)
        failure.full_clean()
        new_instance = self.create(**data)
        return new_instance

    def from_sailthru_error_response(self, msg, failed_instance, sailthru_response):
        assert sailthru_response and not sailthru_response.is_ok()

        error_data = SailthruErrors.get_error_data(sailthru_response)

        data = {
            "message": msg,
            "failed_instance": failed_instance,
            "sailthru_body": sailthru_response.get_body(),
            "sailthru_error_code": error_data["code"],
            "sailthru_error_message": error_data["message"],
            "sailthru_error_description": error_data["description"],
            "sailthru_error_status_code": error_data["response status"],
        }

        failure = self.model(**data)
        failure.full_clean()
        new_instance = self.create(**data)
        if self.should_log_to_sentry(sailthru_response):
            with sentry_sdk.push_scope() as scope:
                scope.set_extra("error_data", data)
                sentry_sdk.capture_message(msg)
        return new_instance

    def from_sailthru_response(self, msg, failed_instance, sailthru_response):
        data = {
            "message": msg,
            "failed_instance": failed_instance,
            "sailthru_body": sailthru_response.get_body(),
        }

        failure = self.model(**data)
        failure.full_clean()
        new_instance = self.create(**data)
        if self.should_log_to_sentry(sailthru_response):
            with sentry_sdk.push_scope() as scope:
                scope.set_extra("data", data)
                sentry_sdk.capture_message(msg)
        return new_instance
