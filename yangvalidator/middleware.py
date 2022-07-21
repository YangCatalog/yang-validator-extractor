from urllib.error import URLError
from urllib.parse import urlencode

import ipware
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from piwikapi.tests.request import FakeRequest
from piwikapi.tracking import PiwikTracker


class ExtendedPiwikTracker(PiwikTracker):
    """ We have to extend this to add the set_user_id """
    user_id = None

    def set_user_id(self, user_id: str):
        self.user_id = user_id

    def _get_request(self, id_site: int):
        url = super()._get_request(id_site)
        if self.user_id:
            url += '&{}'.format(urlencode({'uid': self.user_id}))
        return url


class MatomoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if should_skip(request):
            return response

        site_id = getattr(settings, 'MATOMO_SITE_ID', 1)
        if not site_id:
            return response

        keys_to_serialize = [
            'HTTP_USER_AGENT',
            'REMOTE_ADDR',
            'HTTP_REFERER',
            'HTTP_ACCEPT_LANGUAGE',
            'SERVER_NAME',
            'PATH_INFO',
            'QUERY_STRING',
        ]
        data = {
            'HTTPS': request.is_secure()
        }
        for key in keys_to_serialize:
            if key in request.META:
                data[key] = request.META[key]
        user_id = ''
        if getattr(settings, 'MATOMO_TRACK_USER_ID', None) and request.user and request.user.pk:
            user_id = request.user.pk
        client_ip = ipware.get_client_ip(request)
        try:
            record_analytic(data, client_ip, user_id)
        except URLError:
            pass

        return response


def record_analytic(headers: dict, client_ip: str, user_id: str) -> None:
    """ Send analytics data to Piwik/Matomo """
    # Use "FakeRequest" because we had to serialize the real request
    fake_request = FakeRequest(headers)

    piwik_tracker = ExtendedPiwikTracker(settings.MATOMO_SITE_ID, fake_request)
    piwik_tracker.set_api_url(settings.MATOMO_API_URL)
    if settings.MATOMO_TOKEN_AUTH:
        piwik_tracker.set_token_auth(settings.MATOMO_TOKEN_AUTH)
        piwik_tracker.set_ip(client_ip)
    if getattr(settings, 'MATOMO_TRACK_USER_ID', None) and user_id:
        piwik_tracker.set_user_id(user_id)
    visited_url = fake_request.META['PATH_INFO'][:1000]
    piwik_tracker.do_track_page_view(visited_url)


def should_skip(request: WSGIRequest) -> bool:
    """ Check whether the request is not just a ping. """
    return 'yangvalidator/v2/' not in request.path or 'yangvalidator/v2/ping' in request.path
