from typing import NamedTuple


class GAQLContext(NamedTuple):
    client_customer_id: str
    client_id: str
    client_secret: str
    developer_token: str
    login_customer_id: str
    refresh_token: str
