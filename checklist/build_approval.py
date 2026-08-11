#!/usr/bin/env python3
"""Новые тексты — отдельным файлом на утверждение.

Заказчик утверждает не правки слов, а написанное с нуля: описания, meta-теги,
юридические абзацы, пустые состояния. Такие тексты разбросаны по большому
заданию среди переименований, и выдернуть их глазами тяжело. Здесь они собраны
одни, и по каждому четыре вещи: как сейчас, как надо, где (со снимком) и зачем.

Пояснения «зачем» написаны здесь по-русски заново: в базе часть обоснований
по-польски, а утверждает их человек, читающий по-русски.

Usage: python3 build_approval.py <checklist.json> <crops_dir> <thumbs_dir> <out.html>
"""
import base64
import html
import json
import os
import re
import sys


def esc(s):
    return html.escape(str(s or ""))


# Из склеенной задачи берётся только нужный блок: остальное — правки слов,
# которые здесь не утверждаются.
def member_text(fix, field, member):
    t = (fix.get(field) or "").strip()
    if not t.startswith("— "):
        return t
    m = re.search(rf"— {re.escape(member)} · [^\n]*\n(.*?)(?=\n\n— |\Z)", t, re.S)
    return m.group(1).strip() if m else ""


# id → (страница со снимком, адреса, «как сейчас» по-русски если надо, зачем)
ITEMS = [
 ("01-13", None, "index", ["/"],
  "Заголовок вкладки и описание страницы: PL «Główna», UA «Головна», EN «Home» — служебное слово движка. То же в og:title и og:description.",
  "Это первое, что видит покупатель в поиске Google и при отправке ссылки в мессенджер. Сейчас магазин представляется словом «Главная» — ни бренда, ни города, ни того, что здесь продают. Новый текст называет бренд, ассортимент и Варшаву."),
 ("01-14", None, "index", ["/"],
  "Главного заголовка h1 на странице нет вообще — ни в одной локали. Страница начинается сразу с h2 «Nowości».",
  "Поисковик не понимает, о чём сайт, а экранная читалка не получает точку входа. Предлагается написать h1 и короткий вводный текст о магазине."),
 ("01-03", "01-03", "index", ["/"],
  "Под вкладками блока «Bestsellery» стоит текст чужого бренда: «…Bonpoint creates clothing and accessories for children…» — по-английски во всех трёх локалях.",
  "Абзац скопирован с сайта Bonpoint вместе с их именем. Покупатель читает на польском магазине английскую рекламу чужой марки. Написан свой абзац о том же — про удобство и заботу, но от имени La Petite Bloom."),
 ("09-01", "09-01", "kids", ["/kids", "/footwear", "/niemowleta"],
  "Под заголовком категории «Dzieci» стоит французский текст («Nos collections subliment le quotidien…») — во всех трёх локалях. У остальных категорий описания нет вовсе.",
  "Описание категории — это единственный связный текст на странице каталога: его читает и покупатель, и поисковик. Написан текст для категории «Dzieci» на три языка; по его образцу нужно утвердить и написать остальные семь категорий."),
 ("09-04", None, "kids", ["/kids"],
  "Заголовок вкладки и описание у всех восьми категорий равны названию категории: «Dzieci»/«Dzieci», «Obuwie»/«Obuwie».",
  "В выдаче Google страница категории выглядит как одно слово. Новый шаблон: название + бренд в заголовке, одно продающее предложение в описании. Показан образец для «Dzieci» — по нему заполняются остальные."),
 ("11-22", None, "myszka-maileg-baby-w-sukience-pudrowy-17-6000-00",
  ["/myszka-maileg-baby-w-sukience-pudrowy-17-6000-00"],
  "Описание карточки товара для поисковика дословно повторяет её название. Так на всех ~1300 товарах × 3 языка.",
  "Отдельного описания для поисковой выдачи нет ни у одного товара. Показан образец для мышки Maileg: материал, повод, отправка из Варшавы. По нему программисты зададут шаблон, а тексты потянутся из каталога."),
 ("03-07", None, "contacts", ["/contacts"],
  "Под заголовком «Kontakt» стоит оборванное «LPB Sp. z o.o. ul.» и голые номера NIP/REGON/KRS. В карточке «Skontaktuj się z nami» — адрес регистрации Kasprzaka вместо магазина.",
  "Польский закон (KSH, закон о правах потребителя) требует на сайте полные реквизиты: полное наименование, суд регистрации, капитал. И по вашему решению адреса разведены: Kasprzaka — только регистрация, Mokotowska — магазин и возвраты. Блок реквизитов написан целиком; номер отдела суда — заполнить по выписке KRS."),
 ("19-05", None, "contacts", ["/"],
  "В контактном блоке футера — только «Marcina Kasprzaka 31/119», без компании, города, страны и номеров.",
  "Футер — та самая «постоянная и легкодоступная» форма, где закон об электронных услугах требует реквизиты. Написана одна строка: компания, полный адрес, NIP и KRS."),
 ("19-08", None, "contacts", ["/contacts"],
  "На контактах один адрес почты — hello@lapetitebloom.com.",
  "Регламент и политика конфиденциальности отсылают покупателя на kontakt@ и rodo@, которых на странице контактов нет. Написан блок «Napisz do nas» с ролями: общие вопросы, возвраты, персональные данные. Перед публикацией решить: какие ящики реально работают."),
 ("19-10", None, "contacts", ["/contacts"],
  "Указаны часы работы, но нигде не сказано, когда ждать ответа на письмо или форму.",
  "Покупатель, отправивший вопрос, не знает — ждать сутки или неделю. Написан абзац о сроке ответа; срок рассмотрения рекламаций (14 дней) взят из вашего регламента. Срок первичного ответа помечен «уточнить» — его надо подтвердить."),
 ("19-11", None, "contacts", ["/contacts"],
  "Карточка контактов: адрес, телефон, часы, почта — и всё.",
  "Верификатор Przelewy24 ищет на контактах живую поддержку: часы отдельно от бутика, куда уходит сообщение из формы, отдельный канал для рекламаций. Написан сводный блок «Obsługa klienta», закрывающий эти пункты."),
 ("03-01", "03-01", "contacts", ["/contacts"],
  "Под формой «Masz pytania? Napisz do nas» — только кнопка «Wyślij wiadomość». Никакой информации об обработке данных.",
  "Форма собирает имя, почту и телефон, а art. 13 RODO требует в момент сбора сказать, кто и зачем обрабатывает данные. Написана короткая клаузула со ссылкой на политику конфиденциальности."),
 ("03-04", "03-04", "contacts", ["/contacts"],
  "Выпадающий список темы без подписи и пустого пункта: по умолчанию выбрано «Zwroty», и каждое письмо без смены темы уходит как возврат.",
  "Написана подпись «Temat wiadomości» и переименованы пункты в один стиль (существительные). Мелкие, но новые строки — поэтому на утверждение."),
 ("03-05", None, "contacts", ["/contacts"],
  "Контейнер для соцсетей в карточке контактов пуст — ни одной иконки ни в одной локали.",
  "Для детской марки, живущей из Instagram, это дыра на самой посещаемой странице. Написана подпись «Obserwuj nas»; ссылки на профили — дать ваши."),
 ("03-18", "03-18", "contacts", ["/contacts", "/about"],
  "Описание страниц /contacts и /about для поисковика — одно слово: «Kontakt», «O nas».",
  "Написаны описания в одно-два предложения: на контактах — как связаться и где бутик, на «О нас» — о чём страница."),
 ("03-10", "03-12", "about", ["/about"],
  "Абзац под заголовком секции бутика на /about и сам заголовок: «Sklep»/«Бутік»/«Butik» — три языка называют место тремя разными словами.",
  "Вместе с исправлением заголовка написан новый абзац-приглашение в бутик на Mokotowskiej — тёплый тон, часы, welcome. Утвердить текст абзаца."),
 ("13-03", "13-03", "auth__register", ["/auth/register"],
  "Чекбокс рассылки при регистрации: «Subscribe to our newsletter to stay up to date on Bonpoint News and Special Events» — чужой бренд, по-английски во всех локалях.",
  "Опять Bonpoint. Написан свой текст подписки — о новинках и событиях La Petite Bloom, на трёх языках. Заодно рассылка отделена от обязательного согласия с регламентом: склеивать их запрещает RODO."),
 ("DOC-20", "01-20", "index", ["/", "#subscribe"],
  "В форме подписки на рассылку один обязательный чекбокс склеивает согласие на рассылку и принятие регламента.",
  "Согласие на маркетинг должно быть добровольным и отдельным — это требование RODO, и на нём спотыкаются проверки. Написан новый текст согласия только про рассылку; принятие регламента остаётся в своих местах."),
 ("13-21", None, "auth__forgot-password", ["/auth/forgot"],
  "На странице восстановления пароля — поле e-mail и кнопка «Wyślij». Ни одного слова о том, что произойдёт дальше. Заголовок вкладки — «Wprowadź nowe hasło», хотя нового пароля здесь не вводят.",
  "Покупатель не знает, ждать ли письма. Написано одно пояснительное предложение и переименованы кнопка и заголовок."),
 ("13-07", "13-14", "favorites", ["/favorites"],
  "Пустое избранное: «Lista ulubionych jest pusta.» / «The favorites list is empty.» — и всё.",
  "Сухая констатация без подсказки, что делать. Написан текст-приглашение: нажмите сердечко у товара — он сохранится здесь."),
 ("13-10", "13-10", "search", ["/search"],
  "Страница поиска без запроса показывает: «Wynik wyszukiwania dla zapytania: \"\"» — с пустыми кавычками, в заголовке страницы и вкладки.",
  "Технический шаблон вылез наружу. Написан человеческий текст-приглашение: «Czego szukasz? Wpisz nazwę produktu, markę lub kategorię.»"),
 ("14-14", None, "this-page-does-not-exist-404-probe", ["/любой-несуществующий-адрес"],
  "Страница 404 говорит: «Niestety, nic nie znaleziono dla Twojego zapytania» — текст пустой поисковой выдачи, хотя никакого запроса не было.",
  "Человек попал по битой ссылке, а его спрашивают про «запрос». Написано настоящее сообщение 404: страница не нашлась, вот главная и каталог."),
 ("12-19", "12-19", "special-offers", ["/special-offers"],
  "Подзаголовок страницы акций — снова текст Bonpoint: «…tworzy ubrania i akcesoria dla dzieci…» без подлежащего.",
  "Третье место с текстом чужого бренда. Написан свой подзаголовок: все акции и распродажи La Petite Bloom в одном месте."),
]

# Часть строк на экране не существует — они живут в коде страницы. Для них
# снимок показывает исходник с подсвеченной строкой, и подпись говорит об этом
# прямо, чтобы никто не искал этот текст глазами на сайте.
SHOT_CAPTION = {
 "01-13": "Код главной страницы: подсвечена строка <title>, следом — description",
 "01-14": "Первый заголовок главной — сразу h2 «Nowości»; тега h1 на странице нет",
 "09-04": "Код страницы категории: title и description совпадают дословно",
 "11-22": "Код карточки товара: description дословно повторяет название",
 "13-21": "Форма восстановления пароля целиком — пояснений нет",
 "03-05": "Карточка контактов: под адресом почты пусто — там должны быть соцсети",
}

GDPR_NOTE = (
 "Отдельно: страница «Запросы по персональным данным» (/personal-data-requests) "
 "написана целиком — на ней не хватало половины обязательного по GDPR. Она лежит "
 "готовой страницей в первой части рабочего документа «Что менять на сайте», "
 "там же файлы .docx для чтения и .html для вставки. Утверждается вместе с "
 "остальными документами.")


def img_uri(path):
    if not path or not os.path.exists(path):
        return ""
    return "data:image/jpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()


def main():
    cl_path, crops, spots, out = sys.argv[1:5]
    d = json.load(open(cl_path, encoding="utf-8"))
    F = {f["id"]: f for g in d["groups"] for f in g["fixes"]}

    cards = []
    for n, (fid, member, shot, urls, cur_ru, why_ru) in enumerate(ITEMS, 1):
        f = F.get(fid)
        if not f:
            continue
        member = member or fid
        texts = {}
        for lang, name in (("pl", "Polski"), ("ua", "Українська"), ("en", "English")):
            t = member_text(f, lang, member) or (f.get(lang) or "")
            texts[lang] = (name, t.strip())
        # Снимок всегда показывает место правки, а не страницу целиком:
        # снимок страницы доказывает, что она существует, но не показывает, что
        # менять, — а утверждают именно это. Часть мест снята прицельно
        # (spots), остальные — общей съёмкой (crops).
        crop = (img_uri(os.path.join(spots, fid + ".jpg"))
                or img_uri(os.path.join(crops, member + ".jpg"))
                or img_uri(os.path.join(crops, fid + ".jpg")))
        links = " ".join(
            f'<a href="https://lapetitebloom.com{u}" target="_blank" rel="noopener">{esc(u)}</a>'
            for u in urls if u.startswith("/"))
        lanes = "".join(
            f'<div><h4>{name}</h4><pre>{esc(t)}</pre></div>'
            for name, t in texts.values() if t)
        shot_html = ""
        if crop:
            cap = SHOT_CAPTION.get(fid, "Это место на странице, обведено красным")
            shot_html = (f'<figure><img loading="lazy" src="{crop}" '
                         f'alt="{esc(cap)}"><figcaption>{esc(cap)}</figcaption></figure>')
        cards.append(f"""
<article id="{esc(fid)}">
  <header><span class="num">{n}</span>
    <h2>{esc(f.get('title') or '')}</h2>
    <span class="fid">{esc(fid)}</span></header>
  <p class="where"><b>Где</b> {links}</p>
  {shot_html}
  <div class="pair">
    <div class="was"><b>Как сейчас</b><p>{esc(cur_ru)}</p></div>
    <div class="now"><b>Как надо</b><div class="lanes">{lanes}</div></div>
  </div>
  <p class="why"><b>Зачем и почему</b> {esc(why_ru)}</p>
</article>""")

    page = f"""<title>Новые тексты — на утверждение</title>
<style>
:root{{--ground:#eef0f3;--surface:#fff;--sunken:#e4e7ec;--ink:#171b24;
 --muted:#626b7c;--line:#cfd5de;--hair:#dde2e9;--accent:#2b4b7d;
 --was:#a3352c;--now:#2f6b4f}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{
 --ground:#12151b;--surface:#191d25;--sunken:#0d1015;--ink:#e6e9ef;
 --muted:#9099a8;--line:#333b47;--hair:#262d37;--accent:#8fb0e6;
 --was:#ff9089;--now:#7fc9a4}}}}
:root[data-theme="dark"]{{--ground:#12151b;--surface:#191d25;--sunken:#0d1015;
 --ink:#e6e9ef;--muted:#9099a8;--line:#333b47;--hair:#262d37;--accent:#8fb0e6;
 --was:#ff9089;--now:#7fc9a4}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--ground);color:var(--ink);
 font:15px/1.65 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}}
.sheet{{max-width:960px;margin:0 auto;padding:2.5rem 1.25rem 5rem}}
.mast{{border-bottom:2px solid var(--ink);padding-bottom:1.1rem;margin-bottom:1.6rem}}
.eyebrow{{margin:0 0 .5rem;font-size:.7rem;font-weight:700;letter-spacing:.16em;
 text-transform:uppercase;color:var(--accent)}}
h1{{margin:0 0 .4rem;font-size:clamp(1.4rem,3.2vw,2rem);font-weight:650}}
.lede{{margin:0;color:var(--muted);max-width:70ch}}
article{{background:var(--surface);border:1px solid var(--line);margin:0 0 1rem;
 padding:1rem 1.1rem 1.2rem}}
article header{{display:flex;gap:.6rem;align-items:baseline;flex-wrap:wrap;
 margin-bottom:.4rem}}
.num{{font-weight:700;font-variant-numeric:tabular-nums;color:var(--accent)}}
article h2{{margin:0;font-size:1rem;font-weight:650;flex:1 1 20rem}}
.fid{{font-family:ui-monospace,Menlo,monospace;font-size:.72rem;color:var(--muted)}}
.where{{margin:.2rem 0 .6rem;font-size:.85rem;color:var(--muted)}}
.where b{{font-size:.62rem;letter-spacing:.09em;text-transform:uppercase;color:var(--ink);
 margin-right:.4rem}}
.where a{{color:var(--accent);font-family:ui-monospace,Menlo,monospace;font-size:.78rem;
 text-decoration:none;border-bottom:1px solid var(--line);margin-right:.45rem}}
figure{{margin:.6rem 0;border:1px solid var(--hair);background:#fff}}
figure img{{display:block;width:100%;height:auto}}
figcaption{{padding:.3rem .6rem;font-size:.75rem;color:var(--muted);
 background:var(--sunken)}}
.pair{{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
 margin:.6rem 0}}
.pair>div{{background:var(--surface);padding:.6rem .75rem}}
.pair b{{display:block;font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;
 margin-bottom:.3rem}}
.was b{{color:var(--was)}} .now b{{color:var(--now)}}
.was p{{margin:0;font-size:.9rem}}
.lanes{{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line)}}
.lanes>div{{background:var(--surface);padding:.45rem .6rem;min-width:0}}
.lanes h4{{margin:0 0 .25rem;font-size:.6rem;letter-spacing:.12em;
 text-transform:uppercase;color:var(--accent)}}
.lanes pre{{margin:0;font-family:ui-monospace,Menlo,monospace;font-size:.78rem;
 line-height:1.5;white-space:pre-wrap;overflow-x:auto}}
.why{{margin:.5rem 0 0;font-size:.9rem;color:var(--muted)}}
.why b{{font-size:.62rem;letter-spacing:.09em;text-transform:uppercase;color:var(--ink);
 margin-right:.4rem}}
.gdpr{{margin:1.5rem 0 0;padding:.8rem 1rem;background:var(--sunken);
 border:1px dashed var(--line);font-size:.9rem;color:var(--muted)}}
@media (max-width:760px){{.lanes{{grid-template-columns:1fr}}}}
</style>
<div class="sheet">
  <header class="mast">
    <p class="eyebrow">На утверждение · lapetitebloom.com</p>
    <h1>Новые тексты для сайта</h1>
    <p class="lede">Здесь только то, что написано с нуля, — не исправления слов,
      а новые тексты: описания, юридические абзацы, сообщения покупателю,
      строки для поисковика. {len(cards)} мест. По каждому: как сейчас, как
      предлагается, где это на сайте и зачем. Квадратные скобки
      [уточнить: …] — места, где нужно ваше слово. Утверждение — в общем
      разборе или прямо в чате: достаточно назвать номер.</p>
  </header>
  {''.join(cards)}
  <p class="gdpr">{esc(GDPR_NOTE)}</p>
</div>"""
    open(out, "w", encoding="utf-8").write(page)
    print(f"{out}  {round(len(page.encode()) / 1024)} КБ · пунктов: {len(cards)}")


if __name__ == "__main__":
    main()
