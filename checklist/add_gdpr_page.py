#!/usr/bin/env python3
"""Дописать девятый документ: страница запросов по GDPR.

Восемь документов пришли от заказчика — их перевели и разложили по страницам.
Страница /personal-data-requests документа не имела: она уже стоит на сайте,
и аудит разбирал её по абзацам. Но абзацев, которые надо поменять, там ровно
столько, сколько на странице есть, — вводный меняется (07-08), нижний блок
переписывается целиком (07-07), остаётся один список прав. Держать это списком
правок бессмысленно: проще отдать готовую страницу, как остальные восемь.

Содержание нижнего блока — из правки 07-07: кто администратор данных, что
указать в письме, как мы проверяем личность, что рассмотрение бесплатное,
что месяц может стать тремя, и куда жаловаться. Без этого страница называется
каналом реализации прав по GDPR, не будучи им.

Скрипт идемпотентен: второй запуск ничего не добавляет.

Usage:  python3 add_gdpr_page.py data/translations.json
"""
import json
import sys

DOC_KEY = "9-wnioski-o-dane-osobowe"

BLOCKS = [
    # 1 — вводный абзац. RODO остаётся только в польском: для украинского и
    # английского читателя это непереведённый остаток (правка 07-08).
    ("Jeśli masz pytania dotyczące przetwarzania Twoich danych osobowych lub "
     "chcesz skorzystać ze swoich praw wynikających z RODO, napisz do nas. "
     "Zasady przetwarzania danych opisaliśmy w "
     "[[Polityce prywatności|https://lapetitebloom.com/privacy-policy]].",
     "Якщо у вас є запитання щодо обробки ваших персональних даних або ви "
     "хочете скористатися своїми правами за GDPR (Загальним регламентом про "
     "захист даних), напишіть нам. Правила обробки описані в "
     "[[Політиці конфіденційності|https://lapetitebloom.com/ua/privacy-policy]].",
     "If you have questions about how we process your personal data, or you "
     "would like to exercise your rights under the GDPR, write to us. How we "
     "process data is described in our "
     "[[Privacy policy|https://lapetitebloom.com/en/privacy-policy]]."),

    # 2 — подводка к списку прав.
    ("Możesz przesłać wniosek dotyczący:",
     "Ви можете надіслати запит щодо:",
     "You may submit a request regarding:"),

    # 3–11 — сам список прав. Он на странице стоит и претензий к нему нет:
    # перенесён как есть, выправлена только пунктуация и «email-розсилка».
    ("- dostępu do Twoich danych osobowych;",
     "- доступу до ваших персональних даних;",
     "- access to your personal data;"),
    ("- sprostowania nieprawidłowych lub niekompletnych danych;",
     "- виправлення неточних або неповних даних;",
     "- correction of inaccurate or incomplete data;"),
    ("- usunięcia Twoich danych osobowych;",
     "- видалення ваших персональних даних;",
     "- deletion of your personal data;"),
    ("- ograniczenia przetwarzania danych osobowych;",
     "- обмеження обробки персональних даних;",
     "- restriction of the processing of personal data;"),
    ("- przeniesienia danych osobowych;",
     "- перенесення персональних даних;",
     "- data portability;"),
    ("- wniesienia sprzeciwu wobec przetwarzania danych osobowych;",
     "- заперечення проти обробки персональних даних;",
     "- objection to the processing of personal data;"),
    ("- wycofania zgody na przetwarzanie danych osobowych;",
     "- відкликання згоди на обробку персональних даних;",
     "- withdrawal of consent to the processing of personal data;"),
    ("- wycofania zgody na otrzymywanie newslettera drogą elektroniczną;",
     "- відкликання згоди на отримання розсилки електронною поштою;",
     "- withdrawal of consent to receive the newsletter by email;"),
    ("- innych spraw związanych z przetwarzaniem danych osobowych.",
     "- інших питань, пов’язаних з обробкою персональних даних.",
     "- other matters related to the processing of personal data."),

    # 12–20 — то, чего на странице нет. Правка 07-07.
    ("Jak złożyć wniosek",
     "Як подати запит",
     "How to submit a request"),
    ("Napisz na adres rodo@lapetitebloom.com i podaj: imię i nazwisko, adres "
     "e-mail powiązany z zamówieniem lub kontem, czego dotyczy wniosek oraz — "
     "jeśli sprawa dotyczy newslettera — adres, na który przychodzą "
     "wiadomości. Jeżeli nie będziemy w stanie potwierdzić Twojej tożsamości "
     "na podstawie tych danych, poprosimy o dodatkowe informacje.",
     "Напишіть на адресу rodo@lapetitebloom.com і вкажіть: ім’я та прізвище, "
     "адресу електронної пошти, пов’язану із замовленням або обліковим "
     "записом, суть запиту та — якщо йдеться про розсилку — адресу, на яку "
     "надходять листи. Якщо за цими даними ми не зможемо підтвердити вашу "
     "особу, ми попросимо додаткову інформацію.",
     "Write to rodo@lapetitebloom.com and include: your name, the email "
     "address linked to your order or account, what your request concerns "
     "and — if it relates to the newsletter — the address the messages are "
     "sent to. If we cannot verify your identity from those details, we will "
     "ask for further information."),
    ("Dane, które prześlesz nam w zgłoszeniu, wykorzystamy wyłącznie w celu "
     "rozpatrzenia i obsługi Twojego wniosku.",
     "Дані, які ви надішлете у зверненні, ми використаємо лише для розгляду "
     "та опрацювання вашого запиту.",
     "The data you send us in your request will be used only to review and "
     "handle that request."),

    ("Administrator danych",
     "Контролер даних",
     "Data controller"),
    ("Administratorem danych jest LPB Sp. z o.o., ul. Marcina Kasprzaka "
     "31/119, 01-234 Warszawa.",
     "Контролер персональних даних — LPB Sp. z o.o., ul. Marcina Kasprzaka "
     "31/119, 01-234 Warszawa.",
     "The data controller is LPB Sp. z o.o., ul. Marcina Kasprzaka 31/119, "
     "01-234 Warsaw, Poland."),

    ("Termin i koszt",
     "Термін і вартість",
     "Timescale and cost"),
    ("Rozpatrzenie wniosku jest bezpłatne. Odpowiadamy bez zbędnej zwłoki, "
     "najpóźniej w ciągu miesiąca od otrzymania zgłoszenia. Jeżeli sprawa "
     "jest złożona, możemy przedłużyć ten termin o kolejne dwa miesiące — "
     "poinformujemy Cię o tym wraz z uzasadnieniem.",
     "Розгляд запиту безкоштовний. Ми відповідаємо без зайвої затримки, "
     "щонайпізніше протягом місяця з дня отримання звернення. Якщо справа "
     "складна, ми можемо подовжити цей термін ще на два місяці — і "
     "повідомимо вас про це з поясненням причини.",
     "Handling your request is free of charge. We reply without undue delay "
     "and no later than one month from receipt. If the matter is complex we "
     "may extend that period by a further two months, and we will tell you "
     "why."),

    ("Skarga",
     "Скарга",
     "Complaints"),
    ("Jeżeli uznasz, że przetwarzamy Twoje dane niezgodnie z prawem, możesz "
     "wnieść skargę do Prezesa Urzędu Ochrony Danych Osobowych, ul. Stawki 2, "
     "00-193 Warszawa (uodo.gov.pl).",
     "Якщо ви вважаєте, що ми обробляємо ваші дані неправомірно, ви можете "
     "подати скаргу до Голови Управління охорони персональних даних Польщі "
     "(Prezes Urzędu Ochrony Danych Osobowych), ul. Stawki 2, 00-193 "
     "Warszawa (uodo.gov.pl).",
     "If you believe we are processing your data unlawfully, you may lodge a "
     "complaint with the President of the Personal Data Protection Office "
     "(Prezes Urzędu Ochrony Danych Osobowych), ul. Stawki 2, 00-193 Warsaw, "
     "Poland (uodo.gov.pl)."),
]

NOTES = [
    "Документа от заказчика на эту страницу не было: текст собран из правок "
    "аудита 07-07 и 07-08 и из того, что уже стоит на странице. Список прав "
    "перенесён без изменений — к нему претензий нет.",
    "Заголовок страницы разъезжался по локалям: PL «Kontakt w sprawie danych "
    "osobowych» обещал контакт, EN «Personal data requests» — запросы. Взято "
    "второе во всех трёх: страница не про адрес почты, а про подачу запроса.",
    "«RODO» остаётся только в польском. В UA и EN — «GDPR», в украинском с "
    "расшифровкой при первом упоминании, как в остальных восьми документах.",
    "Отдельно от текста: на страницу не ведёт ни одна ссылка — её нет ни в "
    "футере, ни в меню, ни в политике конфиденциальности. Пока ссылки нет, "
    "готовый текст никто не прочитает. Правка 07-06, делают программисты.",
    "Срок «месяц, в сложных случаях +2» и право жалобы в UODO — это ст. 12 "
    "п. 3 и ст. 77 GDPR. Формулировки стандартные, но перед публикацией их "
    "стоит показать юристу вместе с остальным пакетом.",
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/translations.json"
    data = json.load(open(path, encoding="utf-8"))

    if any(d.get("doc") == DOC_KEY for d in data["documents"]):
        print("девятый документ уже на месте — ничего не меняю")
        return

    doc = {
        "doc": DOC_KEY,
        "title": "Запросы по персональным данным",
        "target_path": "/personal-data-requests",
        "title_pl": "Wnioski dotyczące danych osobowych",
        "title_ua": "Запити щодо персональних даних",
        "title_en": "Personal data requests",
        "notes": NOTES,
        "applied_decisions": [
            "rodo@lapetitebloom.com — адрес для вопросов по данным "
            "(решение заказчика)",
            "Kasprzaka 31/119 — адрес фирмы в реквизитах (решение заказчика)",
        ],
        "page": {
            "pl": "https://lapetitebloom.com/personal-data-requests",
            "ua": "https://lapetitebloom.com/ua/personal-data-requests",
            "en": "https://lapetitebloom.com/en/personal-data-requests",
        },
        "links": [],
        "blocks": [{"n": i, "pl": pl, "ua": ua, "en": en}
                   for i, (pl, ua, en) in enumerate(BLOCKS, 1)],
    }

    data["documents"].append(doc)
    data["total_blocks"] = sum(len(d["blocks"]) for d in data["documents"])

    json.dump(data, open(path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"добавлен {DOC_KEY}: {len(doc['blocks'])} блоков × 3 языка")
    print(f"всего документов: {len(data['documents'])}, "
          f"блоков: {data['total_blocks']}")


if __name__ == "__main__":
    main()
