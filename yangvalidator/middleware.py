from urllib.error import URLError

import ipware
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from piwikapi.tests.request import FakeRequest
from piwikapi.tracking import PiwikTracker


class MatomoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if should_skip(request):
            return response

        site_id = getattr(settings, 'MATOMO_SITE_ID')
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
        client_ip = ipware.get_client_ip(request)
        try:
            record_analytic(data, client_ip)
        except URLError:
            pass

        return response


def record_analytic(headers: dict, client_ip: str) -> None:
    """ Send analytics data to Piwik/Matomo """
    # Use "FakeRequest" because we had to serialize the real request
    fake_request = FakeRequest(headers)

    piwik_tracker = PiwikTracker(settings.MATOMO_SITE_ID, fake_request)
    piwik_tracker.set_api_url(settings.MATOMO_API_URL)
    if settings.MATOMO_TOKEN_AUTH:
        piwik_tracker.set_token_auth(settings.MATOMO_TOKEN_AUTH)
        piwik_tracker.set_ip(client_ip)
    visited_url = fake_request.META['PATH_INFO'][:1000]
    piwik_tracker.do_track_page_view('API yangvalidator {}'.format(visited_url))


def should_skip(request: WSGIRequest) -> bool:
    """ Check whether the request is not just a ping. """
    return 'yangvalidator/v2/' not in request.path or 'v2/ping' in request.path or 'v2/versions' in request.path
