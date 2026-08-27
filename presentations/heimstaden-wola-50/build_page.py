#!/usr/bin/env python3
"""Собирает одностраничную веб-версию презентации со встроенными фотографиями."""
import base64
import pathlib

SRC = pathlib.Path(__file__).with_name("photos")
OUT = pathlib.Path(__file__).with_name("grzybowska-49.html")


def uri(name):
    data = base64.b64encode((SRC / name).read_bytes()).decode()
    return f"data:image/jpeg;base64,{data}"


PHOTOS = [
    ("02.jpg", "Гостиная", "23,67 м², окна в пол, выход на лоджию", True),
    ("03.jpg", "Гостиная и обеденная зона", "Справа — вход в изолированную спальню", False),
    ("01.jpg", "Кухня, открытая в гостиную", "Индукционная плита, духовка, вытяжка, посудомоечная машина", False),
    ("04.jpg", "Спальня", "10,72 м², кровать 160 × 200 см, встроенный шкаф", False),
    ("06.jpg", "Ванная комната", "7,45 м², ванна, стиральная машина, полотенцесушитель", False),
    ("05.jpg", "Прихожая и кухонный блок", "Встроенные шкафы, видеодомофон, кондиционер", False),
    ("07.jpg", "Grzybowska 49", "Дом 2022 года: ресепшн, охрана, велопарковка, зелёный двор", False),
]

SPECS = [
    ("Площадь", "50,99 м²"),
    ("Комнаты", "Гостиная с кухней + изолированная спальня"),
    ("Этаж", "1-й, дом с лифтом"),
    ("Год постройки", "2022"),
    ("Лоджия", "5,34 м²"),
    ("Кондиционер", "Есть"),
    ("Интернет", "Включён, до 550 Мбит/с"),
    ("Свободна", "с 26 августа 2026 г."),
    ("Питомцы", "Разрешены"),
    ("Договор", "Напрямую с собственником, без комиссии"),
]

ROOMS = [
    ("1", "Прихожая и кухонная зона", "9,13"),
    ("2", "Гостиная", "23,67"),
    ("3", "Ванная комната", "7,45"),
    ("4", "Спальня", "10,72"),
    ("5", "Лоджия", "5,34"),
]

KIT = [
    ("Кухня", "Индукционная плита, духовка, вытяжка, посудомоечная машина, холодильник с морозильной камерой, обеденный стол со стульями"),
    ("Гостиная", "Диван, тумба под ТВ, встроенные шкафы, окна в пол с выходом на лоджию"),
    ("Спальня", "Кровать 160 × 200 см с матрасом, шкаф, прикроватные тумбы"),
    ("Ванная", "Ванна, раковина с тумбой, стиральная машина, полотенцесушитель"),
    ("В квартире", "Кондиционер, интернет до 550 Мбит/с в стоимости аренды"),
    ("В доме", "Лифт, ресепшн, круглосуточная охрана, велопарковка, подземный гараж по запросу"),
]

PLACES = [
    ("Метро Rondo Daszyńskiego", "линия M2, несколько минут пешком"),
    ("Browary Warszawskie", "рестораны, магазины, площадь с фонтанами"),
    ("Fabryka Norblina", "кинотеатр, фудкорт, рынок и музей"),
    ("Деловой центр Воли", "Warsaw Unit, Skyliner, Generation Park"),
    ("Центр города", "Дворец культуры — около 2 км"),
]

LISTING = "https://oferty.heimstaden.pl/warszawa/offers/42216-2-pokojowe-5099-m2-balkon-internet-w-cenie-bezposrednio"
TOUR = "https://my.matterport.com/show/?m=QdbufVrYA3d"

gallery = "\n".join(
    f'''      <figure class="shot{' shot--wide' if wide else ''}">
        <button class="shot__btn" type="button" data-src="{uri(f)}" data-caption="{cap}">
          <img src="{uri(f)}" alt="{cap}" loading="lazy" width="1200" height="800">
        </button>
        <figcaption><b>{cap}</b><span>{sub}</span></figcaption>
      </figure>'''
    for f, cap, sub, wide in PHOTOS
)

specs = "\n".join(
    f'        <div class="spec"><dt>{k}</dt><dd>{v}</dd></div>' for k, v in SPECS
)

rooms = "\n".join(
    f'''          <li><span class="num">{n}</span><span class="room">{name}</span><span class="area">{a} м²</span></li>'''
    for n, name, a in ROOMS
)

kit = "\n".join(
    f'        <div class="kit"><h3>{k}</h3><p>{v}</p></div>' for k, v in KIT
)

places = "\n".join(
    f'          <li><b>{k}</b><span>{v}</span></li>' for k, v in PLACES
)

HTML = f'''<title>Grzybowska 49 · m0104</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Golos+Text:wght@400;500;600;700&family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,500;1,7..72,400&display=swap">

<style>
:root {{
  --paper:  #ffffff;
  --raise:  #f4f3f0;
  --sink:   #edebe6;
  --line:   #e0ded7;
  --ink:    #17181b;
  --muted:  #6d6a63;
  --accent: #cf4e1c;
  --shadow: 0 1px 2px rgba(23,24,27,.05), 0 12px 32px -18px rgba(23,24,27,.28);
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --paper:  #141517;
    --raise:  #1c1e21;
    --sink:   #202327;
    --line:   #2e3237;
    --ink:    #eceae5;
    --muted:  #99958d;
    --accent: #f2733e;
    --shadow: 0 1px 2px rgba(0,0,0,.4), 0 14px 36px -20px rgba(0,0,0,.7);
  }}
}}
:root[data-theme="dark"] {{
  --paper:  #141517;
  --raise:  #1c1e21;
  --sink:   #202327;
  --line:   #2e3237;
  --ink:    #eceae5;
  --muted:  #99958d;
  --accent: #f2733e;
  --shadow: 0 1px 2px rgba(0,0,0,.4), 0 14px 36px -20px rgba(0,0,0,.7);
}}

* {{ box-sizing: border-box; }}

body {{
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: "Golos Text", "Segoe UI", system-ui, sans-serif;
  font-size: 16px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}}

.wrap {{
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 24px;
}}

.eyebrow {{
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .16em;
  text-transform: uppercase;
  color: var(--accent);
  margin: 0;
}}

h1 {{
  font-family: "Golos Text", sans-serif;
  font-size: clamp(34px, 6vw, 58px);
  font-weight: 700;
  letter-spacing: -.03em;
  line-height: 1.04;
  text-wrap: balance;
  margin: 14px 0 0;
}}

h2 {{
  font-family: "Golos Text", sans-serif;
  font-size: clamp(21px, 3vw, 27px);
  font-weight: 600;
  letter-spacing: -.02em;
  text-wrap: balance;
  margin: 0;
}}

h3 {{
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -.01em;
  margin: 0;
}}

p {{ margin: 0; }}

.lede {{
  font-family: Literata, Georgia, serif;
  font-size: 17px;
  line-height: 1.65;
  color: var(--muted);
  max-width: 60ch;
}}

/* ---------- header ---------- */

header {{ padding: clamp(46px, 8vw, 92px) 0 0; }}

.addr {{
  margin-top: 18px;
  font-size: 17px;
  color: var(--muted);
}}

.chips {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 26px;
  padding: 0;
  list-style: none;
}}
.chips li {{
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 13.5px;
  font-weight: 500;
  color: var(--muted);
  background: var(--raise);
}}

/* ---------- verdict ---------- */

.verdict {{
  margin-top: clamp(44px, 7vw, 76px);
  display: grid;
  gap: 28px;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  align-items: start;
  background: var(--sink);
  border-radius: 14px;
  padding: clamp(24px, 4vw, 38px);
}}
.tally {{ display: grid; gap: 18px; }}
.tally div {{ display: flex; align-items: baseline; gap: 12px; }}
.tally b {{
  font-size: 30px;
  font-weight: 700;
  letter-spacing: -.03em;
  font-variant-numeric: tabular-nums;
  color: var(--accent);
  min-width: 2.4ch;
}}
.tally span {{ font-size: 14.5px; color: var(--muted); }}

/* ---------- sections ---------- */

section {{ margin-top: clamp(56px, 9vw, 104px); }}

.head {{
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 28px;
}}
.head span {{
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--muted);
}}

/* ---------- specs ---------- */

.specs {{
  margin: 0;
  display: grid;
  gap: 0;
}}
.spec {{
  display: grid;
  grid-template-columns: minmax(150px, 232px) 1fr;
  gap: 20px;
  padding: 13px 0;
  border-bottom: 1px solid var(--line);
}}
.spec dt {{ color: var(--muted); font-size: 14.5px; }}
.spec dd {{ margin: 0; font-weight: 500; }}

/* ---------- plan ---------- */

.plan {{
  display: grid;
  gap: clamp(24px, 4vw, 44px);
  grid-template-columns: 1fr;
  align-items: start;
}}
@media (min-width: 760px) {{ .plan {{ grid-template-columns: 1fr 1fr; }} }}

.plan img {{
  width: 100%;
  max-width: 430px;
  height: auto;
  display: block;
  margin-inline: auto;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 12px;
}}
.plan ol {{ margin: 0; padding: 0; list-style: none; display: grid; gap: 2px; }}
.plan li {{
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 13px 0;
  border-bottom: 1px solid var(--line);
}}
.num {{
  flex: none;
  width: 26px; height: 26px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  display: grid;
  place-items: center;
}}
.room {{ flex: 1; font-weight: 500; }}
.area {{ color: var(--muted); font-variant-numeric: tabular-nums; font-size: 14.5px; }}
.plan .note {{ margin-top: 18px; font-size: 14px; color: var(--muted); }}

/* ---------- gallery ---------- */

.gallery {{
  display: grid;
  gap: 22px;
  grid-template-columns: 1fr;
}}
@media (min-width: 720px) {{
  .gallery {{ grid-template-columns: 1fr 1fr; }}
  .shot--wide {{ grid-column: 1 / -1; }}
}}
.shot {{ margin: 0; }}
.shot__btn {{
  display: block;
  width: 100%;
  padding: 0;
  border: 0;
  border-radius: 12px;
  overflow: hidden;
  background: var(--sink);
  cursor: zoom-in;
  box-shadow: var(--shadow);
}}
.shot__btn img {{
  display: block;
  width: 100%;
  height: auto;
  transition: transform .5s cubic-bezier(.2,.7,.3,1);
}}
.shot__btn:hover img {{ transform: scale(1.02); }}
.shot__btn:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 3px; }}
figcaption {{ margin-top: 12px; display: grid; gap: 3px; }}
figcaption b {{ font-size: 15px; font-weight: 600; }}
figcaption span {{ font-size: 14px; color: var(--muted); }}

/* ---------- kit + places ---------- */

.kits {{ display: grid; gap: 1px; }}
.kit {{
  display: grid;
  grid-template-columns: 1fr;
  gap: 6px;
  padding: 18px 0;
  border-bottom: 1px solid var(--line);
}}
@media (min-width: 700px) {{
  .kit {{ grid-template-columns: minmax(150px, 232px) 1fr; gap: 20px; align-items: baseline; }}
}}
.kit p {{ color: var(--muted); font-size: 15px; }}

.places {{ margin: 0; padding: 0; list-style: none; display: grid; gap: 1px; }}
.places li {{
  display: grid;
  grid-template-columns: 1fr;
  gap: 4px;
  padding: 16px 0;
  border-bottom: 1px solid var(--line);
}}
@media (min-width: 700px) {{
  .places li {{ grid-template-columns: minmax(150px, 300px) 1fr; gap: 20px; align-items: baseline; }}
}}
.places span {{ color: var(--muted); font-size: 15px; }}

/* ---------- links ---------- */

.links {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(248px, 1fr)); }}
.card {{
  display: block;
  padding: 20px 22px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--raise);
  color: inherit;
  text-decoration: none;
  transition: border-color .18s, transform .18s;
}}
a.card:hover {{ border-color: var(--accent); transform: translateY(-2px); }}
a.card:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 3px; }}
.card small {{
  display: block;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .13em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 7px;
}}
.card b {{ font-size: 16px; font-weight: 600; word-break: break-word; }}

footer {{
  margin: clamp(56px, 9vw, 96px) 0 64px;
  padding-top: 22px;
  border-top: 1px solid var(--line);
  font-size: 13.5px;
  color: var(--muted);
  display: grid;
  gap: 6px;
}}

/* ---------- lightbox ---------- */

dialog {{
  border: 0;
  padding: 0;
  background: transparent;
  max-width: 96vw;
  max-height: 96vh;
}}
dialog::backdrop {{ background: rgba(10,10,12,.9); }}
dialog img {{ display: block; max-width: 96vw; max-height: 84vh; border-radius: 10px; }}
dialog p {{ margin-top: 12px; color: #f2f0ec; font-size: 14.5px; text-align: center; }}
.close {{
  position: fixed;
  top: 16px; right: 18px;
  width: 40px; height: 40px;
  border-radius: 50%;
  border: 0;
  background: rgba(255,255,255,.14);
  color: #fff;
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
}}
.close:hover {{ background: rgba(255,255,255,.26); }}

@media (prefers-reduced-motion: reduce) {{
  * {{ transition: none !important; animation: none !important; }}
}}
</style>

<div class="wrap">

  <header>
    <p class="eyebrow">Heimstaden · Варшава, Воля</p>
    <h1>50,99 м²,<br>две комнаты</h1>
    <p class="addr">ул. Гжибовска 49, квартира m0104 · 00-844 Варшава</p>
    <ul class="chips">
      <li>1-й этаж</li><li>Лоджия 5,34 м²</li><li>Кондиционер</li>
      <li>Меблирована</li><li>Интернет включён</li><li>Питомцы разрешены</li>
    </ul>
  </header>

  <div class="verdict">
    <div>
      <h2>Единственный вариант на Воле</h2>
      <p class="lede" style="margin-top:12px">
        В каталоге Heimstaden по Варшаве 159 квартир. В районе Воля — 24, и все по одному
        адресу, Grzybowska 49. Порог «от 50 м²» проходит только эта квартира; остальные в доме
        меньше: 2-комнатные 40,7–41,8 м², студии 30,3–38,9 м².
      </p>
    </div>
    <div class="tally">
      <div><b>159</b><span>квартир Heimstaden<br>по всей Варшаве</span></div>
      <div><b>24</b><span>из них в районе Воля<br>— все на Grzybowska 49</span></div>
      <div><b>1</b><span>квартира от 50 м²<br>— m0104, 50,99 м²</span></div>
    </div>
  </div>

  <section>
    <div class="head"><h2>Характеристики</h2><span>Объект m0104</span></div>
    <dl class="specs">
{specs}
    </dl>
  </section>

  <section>
    <div class="head"><h2>Планировка</h2><span>1-й этаж · 50,99 м²</span></div>
    <div class="plan">
      <div>
        <ol>
{rooms}
        </ol>
        <p class="note">
          Нумерация соответствует плану. Кухня открыта в гостиную, спальня изолированная,
          со встроенным шкафом. Размеры на плане ориентировочные.
        </p>
      </div>
      <img src="{uri('08.jpg')}" alt="Поэтажный план квартиры m0104" width="1024" height="1448">
    </div>
  </section>

  <section>
    <div class="head"><h2>Фотографии</h2><span>Все снимки объявления</span></div>
    <div class="gallery">
{gallery}
    </div>
  </section>

  <section>
    <div class="head"><h2>Оснащение</h2><span>Квартира сдаётся меблированной</span></div>
    <div class="kits">
{kit}
    </div>
  </section>

  <section>
    <div class="head"><h2>Локация</h2><span>Историческая Воля</span></div>
    <ul class="places">
{places}
    </ul>
  </section>

  <section>
    <div class="head"><h2>Объявление и контакты</h2><span>Напрямую от собственника</span></div>
    <div class="links">
      <a class="card" href="{LISTING}" target="_blank" rel="noopener">
        <small>Объявление</small><b>oferty.heimstaden.pl · № 42216</b>
      </a>
      <a class="card" href="{TOUR}" target="_blank" rel="noopener">
        <small>3D-тур по квартире</small><b>Matterport</b>
      </a>
      <a class="card" href="tel:+48884204735">
        <small>Телефон</small><b>+48 884 204 735</b>
      </a>
      <a class="card" href="mailto:witaj@heimstaden.pl">
        <small>Почта</small><b>witaj@heimstaden.pl</b>
      </a>
    </div>
  </section>

  <footer>
    <span>Данные и наличие — на 26 августа 2026 года, по каталогу oferty.heimstaden.pl.</span>
    <span>Стоимость аренды и платежи в подборку не включены — уточняйте у собственника.</span>
  </footer>

</div>

<dialog id="box">
  <button class="close" type="button" aria-label="Закрыть">&times;</button>
  <img alt="">
  <p></p>
</dialog>

<script>
(function () {{
  var box = document.getElementById('box');
  var img = box.querySelector('img');
  var cap = box.querySelector('p');

  document.querySelectorAll('.shot__btn').forEach(function (btn) {{
    btn.addEventListener('click', function () {{
      img.src = btn.dataset.src;
      img.alt = btn.dataset.caption;
      cap.textContent = btn.dataset.caption;
      box.showModal();
    }});
  }});

  box.querySelector('.close').addEventListener('click', function () {{ box.close(); }});
  box.addEventListener('click', function (e) {{ if (e.target === box) box.close(); }});
}})();
</script>
'''

OUT.write_text(HTML, encoding="utf-8")
print(f"written: {OUT}  ({OUT.stat().st_size/1024/1024:.2f} MB)")
