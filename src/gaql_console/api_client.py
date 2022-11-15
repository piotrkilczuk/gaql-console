import importlib
from typing import Iterator

from google.ads.googleads import client as ads_client, errors as ads_errors
from google.oauth2 import credentials

from gaql_console import context, exceptions


# @TODO: Make me customizable
API_VERSION = "v12"


def import_for_version(suffix: str):
    module_path, member = suffix.rsplit(".", maxsplit=1)
    path = f"google.ads.googleads.{API_VERSION}.{module_path}"
    module = importlib.import_module(path)
    member = getattr(module, member)
    return member


GoogleAdsRow = import_for_version("services.types.google_ads_service.GoogleAdsRow")


class GAQLClient:
    _context: context.GAQLContext
    _client: ads_client.GoogleAdsClient

    def __init__(self, _context: context.GAQLContext):
        self._context = _context
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
            version=API_VERSION,
        )

    def query(self, gaql: str) -> Iterator[GoogleAdsRow]:
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


def client(_context: context.GAQLContext) -> ads_client.GoogleAdsClient:
    return ads_client.GoogleAdsClient(
        credentials=None,
        developer_token=_context.developer_token,
        version=API_VERSION,
    )
