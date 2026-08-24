"""Минимальный клиент BaseLinker API + создание заказа БЕЗ списания со склада.

Токен берётся из переменной окружения BL_TOKEN (в код его не кладём).

    export BL_TOKEN="xxxxx-xxxxx-XXXX..."
    python3 -m baselinker.client --demo
"""

import json
import os
import time
import urllib.parse
import urllib.request

API_URL = "https://api.baselinker.com/connector.php"


class BaseLinkerError(RuntimeError):
    pass


def call(method, parameters=None, token=None):
    """Один вызов BaseLinker API. Возвращает распарсенный ответ."""
    token = token or os.environ.get("BL_TOKEN")
    if not token:
        raise BaseLinkerError("Не задан BL_TOKEN")

    body = urllib.parse.urlencode(
        {"method": method, "parameters": json.dumps(parameters or {})}
    ).encode()
    req = urllib.request.Request(
        API_URL, data=body, headers={"X-BLToken": token}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())

    if data.get("status") != "SUCCESS":
        raise BaseLinkerError(
            "%s: %s (%s)"
            % (method, data.get("error_message"), data.get("error_code"))
        )
    return data


def order_line(name, sku, price_brutto, quantity, ean="", tax_rate=23, weight=0):
    """Позиция заказа БЕЗ привязки к каталогу.

    Ключевой момент: product_id = "" (пусто). Тогда BaseLinker не находит
    товар в каталоге и НЕ трогает складские остатки.
    Если сюда подставить реальный product_id — остаток спишется сразу же.
    """
    return {
        "storage": "db",
        "storage_id": 0,
        "product_id": "",   # <-- пусто = нет списания со склада
        "variant_id": 0,
        "name": name,
        "sku": sku,
        "ean": ean,
        "price_brutto": price_brutto,
        "tax_rate": tax_rate,
        "quantity": quantity,
        "weight": weight,
    }


def create_paid_online_order(
    products,
    status_id,
    email,
    currency="PLN",
    payment_method="Online",
    user_login="",
    phone="",
    delivery_method="",
    delivery_price=0,
    delivery_fullname="",
    delivery_address="",
    delivery_city="",
    delivery_postcode="",
    delivery_country_code="PL",
    admin_comments="",
    user_comments="",
    custom_source_id=None,
    token=None,
):
    """Создаёт оплаченный онлайн-заказ в нужном статусе.

    Ничего не печатает и не списывает со склада — addOrder сам по себе
    не генерирует ни чеков, ни фактур (want_invoice = 0).
    """
    params = {
        "order_status_id": status_id,
        "date_add": int(time.time()),
        "currency": currency,
        "payment_method": payment_method,
        "payment_method_cod": False,
        "paid": 1,               # оплачен: BaseLinker сам добавит полную оплату
        "email": email,
        "user_login": user_login,
        "phone": phone,
        "delivery_method": delivery_method,
        "delivery_price": delivery_price,
        "delivery_fullname": delivery_fullname,
        "delivery_address": delivery_address,
        "delivery_city": delivery_city,
        "delivery_postcode": delivery_postcode,
        "delivery_country_code": delivery_country_code,
        "want_invoice": 0,       # без фактуры
        "admin_comments": admin_comments,
        "user_comments": user_comments,
        "products": products,
    }
    if custom_source_id is not None:
        params["custom_source_id"] = custom_source_id

    return call("addOrder", params, token=token)["order_id"]


# --- параметры конкретного аккаунта (La Peitte Bloom) ---
INVENTORY_ID = 89839
WAREHOUSE_ID = 123819                    # bl_123819 "Shop"
STATUS_ONLINE_PAID_NEW = 507215          # "Online — opłacone / nowe"


def _demo():
    order_id = create_paid_online_order(
        products=[
            order_line(
                name="TEST API - nie sprzedawac",
                sku="TEST-API-001",
                ean="5901234123457",
                price_brutto=10.00,
                quantity=2,
                weight=0.5,
            )
        ],
        status_id=STATUS_ONLINE_PAID_NEW,
        email="test-api@example.com",
        payment_method="TEST API",
        delivery_method="TEST - brak wysylki",
        delivery_fullname="TEST API - do usuniecia",
        delivery_address="ul. Testowa 1",
        delivery_city="Warszawa",
        delivery_postcode="00-001",
        admin_comments="ZAMOWIENIE TESTOWE (API). Do usuniecia.",
    )
    print("order_id =", order_id)


if __name__ == "__main__":
    _demo()
