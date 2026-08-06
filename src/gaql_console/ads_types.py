import importlib
from typing import Union

# @TODO: Make me customizable
API_VERSION = "v22"


def import_for_version(suffix: str):
    module_path, member = suffix.rsplit(".", maxsplit=1)
    path = f"google.ads.googleads.{API_VERSION}.{module_path}"
    module = importlib.import_module(path)
    member = getattr(module, member)
    return member


GoogleAdsRow = import_for_version("services.types.google_ads_service.GoogleAdsRow")

GoogleAdsScalar = Union[str, int, float, bool]

GoogleAdsNestedValue = Union[GoogleAdsScalar, list[GoogleAdsScalar], "GoogleAdsNestedDict"]
GoogleAdsNestedDict = dict[str, GoogleAdsNestedValue]
