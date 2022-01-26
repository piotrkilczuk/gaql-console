from importlib import import_module
from typing import Iterator

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.oauth2.credentials import Credentials

from gaql_console.context import GAQLContext
from gaql_console.exceptions import QueryException

# @TODO: Make me customizable
API_VERSION = "v9"


def import_for_version(suffix: str):
    module_path, member = suffix.rsplit(".", maxsplit=1)
    path = f"google.ads.googleads.{API_VERSION}.{module_path}"
    module = import_module(path)
    member = getattr(module, member)
    return member


GoogleAdsRow = import_for_version("services.types.google_ads_service.GoogleAdsRow")


class GAQLClient:
    _context: GAQLContext
    _client: GoogleAdsClient

    def __init__(self, context: GAQLContext):
        self._context = context
        credentials = Credentials.from_authorized_user_info(
            {
                "refresh_token": context.refresh_token,
                "client_id": context.client_id,
                "client_secret": context.client_secret,
            }
        )
        self._client = GoogleAdsClient(
            credentials=credentials,
            developer_token=context.developer_token,
            login_customer_id=context.login_customer_id,
            version=API_VERSION,
        )

    def query(self, gaql: str) -> Iterator[GoogleAdsRow]:
        # keep this in scope - see https://github.com/googleads/google-ads-python/issues/384
        service = self._client.get_service("GoogleAdsService")

        try:
            streaming_response_iterator = service.search_stream(
                customer_id=self._context.client_customer_id, query=gaql
            )
        except GoogleAdsException as exc:
            raise QueryException(exc.failure.errors[0].message)

        for response in streaming_response_iterator:
            for result in response.results:
                yield result


def client(context: GAQLContext) -> GoogleAdsClient:
    return GoogleAdsClient(
        credentials=None,
        developer_token=context.developer_token,
        version=API_VERSION,
    )
