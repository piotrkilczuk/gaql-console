import importlib
import os
from typing import Iterator

from google.ads.googleads import client as ads_client, errors as ads_errors
from google.oauth2 import credentials

from gaql_console import context, exceptions


DEFAULT_API_VERSION = "v23"


class GAQLClient:
    _context: context.GAQLContext
    _client: ads_client.GoogleAdsClient
    _api_version: str

    def __init__(self, _context: context.GAQLContext, api_version: str = DEFAULT_API_VERSION):
        self._context = _context
        self._api_version = api_version
        _credentials = credentials.Credentials.from_authorized_user_info(
            {
                "refresh_token": _context.refresh_token,
                "client_id": _context.client_id,
                "client_secret": _context.client_secret,
            }
        )
        self._client = ads_client.GoogleAdsClient(
            credentials=_credentials,
            developer_token=_context.developer_token,
            login_customer_id=_context.login_customer_id,
            version=self._api_version,
        )

    def query(self, gaql: str) -> Iterator:
        # keep this in scope - see https://github.com/googleads/google-ads-python/issues/384
        service = self._client.get_service("GoogleAdsService")

        try:
            streaming_response_iterator = service.search_stream(
                customer_id=self._context.client_customer_id, query=gaql
            )
        except ads_errors.GoogleAdsException as exc:
            raise exceptions.QueryException(exc.failure.errors[0].message)

        for response in streaming_response_iterator:
            for result in response.results:
                yield result
