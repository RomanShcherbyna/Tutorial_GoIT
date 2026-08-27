/**
 * Презентация: квартиры Heimstaden от 50 м² в районе Воля (Варшава).
 * Данные собраны с oferty.heimstaden.pl / api.flater.pl (см. data.json).
 * Цены в презентацию намеренно не выводятся.
 */
const pptxgen = require("pptxgenjs");
const path = require("path");

const INK = "1C1B19";
const PAPER = "FFFFFF";
const TINT = "F1ECE6";
const ACCENT = "E4572E";
const MUTED = "6E6A66";
const LIGHT = "C9C3BC";

const H = "Cambria";
const B = "Calibri";

const W = 13.333;
const HT = 7.5;

const P = (n) => path.join(__dirname, "photos", n);

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Heimstaden offer digest";
pres.title = "Квартиры от 50 м² на Воле — Heimstaden, Варшава";

/* ---------- helpers ---------- */

function slideTitle(s, text, opts = {}) {
  s.addText(text, {
    isTextBox: true,
    x: 0.7,
    y: opts.y || 0.5,
    w: opts.w || 8.5,
    h: 0.9,
    fontFace: H,
    fontSize: opts.size || 34,
    bold: true,
    color: opts.color || INK,
    margin: 0,
    valign: "middle",
  });
}

function kicker(s, text, opts = {}) {
  s.addText(text.toUpperCase(), {
    isTextBox: true,
    x: opts.x || 0.7,
    y: opts.y || 0.16,
    w: opts.w || 8.5,
    h: 0.32,
    fontFace: B,
    fontSize: 11,
    bold: true,
    charSpacing: 2.2,
    color: opts.color || ACCENT,
    margin: 0,
    valign: "middle",
  });
}

function numberBadge(s, n, x, y, opts = {}) {
  s.addShape(pres.ShapeType.ellipse, {
    x,
    y,
    w: 0.42,
    h: 0.42,
    fill: { color: opts.fill || ACCENT },
  });
  s.addText(String(n), {
    isTextBox: true,
    x,
    y,
    w: 0.42,
    h: 0.42,
    fontFace: B,
    fontSize: 13,
    bold: true,
    color: opts.color || "FFFFFF",
    align: "center",
    valign: "middle",
    margin: 0,
  });
}

/* Полноэкранное фото с тёмной подписью снизу. */
function photoSlide(file, caption, sub) {
  const s = pres.addSlide();
  s.background = { color: INK };
  s.addImage({ path: P(file), x: 0, y: 0, w: W, h: HT, sizing: { type: "cover", w: W, h: HT } });
  s.addShape(pres.ShapeType.rect, {
    x: 0,
    y: HT - 1.5,
    w: W,
    h: 1.5,
    fill: { color: INK, transparency: 18 },
  });
  s.addText(caption, {
    isTextBox: true,
    x: 0.7,
    y: HT - 1.18,
    w: 9.5,
    h: 0.5,
    fontFace: H,
    fontSize: 24,
    bold: true,
    color: "FFFFFF",
    margin: 0,
    valign: "middle",
  });
  s.addText(sub, {
    isTextBox: true,
    x: 0.7,
    y: HT - 0.7,
    w: 9.5,
    h: 0.36,
    fontFace: B,
    fontSize: 13,
    color: LIGHT,
    margin: 0,
    valign: "middle",
  });
  return s;
}

/* ---------- 1. Титул ---------- */
{
  const s = pres.addSlide();
  s.background = { color: INK };
  s.addImage({
    path: P("07.jpg"),
    x: 6.9,
    y: 0,
    w: 6.433,
    h: HT,
    sizing: { type: "cover", w: 6.433, h: HT },
  });

  s.addText("HEIMSTADEN · ВАРШАВА", {
    isTextBox: true,
    x: 0.85,
    y: 1.35,
    w: 5.6,
    h: 0.35,
    fontFace: B,
    fontSize: 12,
    bold: true,
    charSpacing: 2.6,
    color: ACCENT,
    margin: 0,
  });
  s.addText("Квартиры от 50 м²\nв районе Воля", {
    isTextBox: true,
    x: 0.85,
    y: 1.95,
    w: 5.85,
    h: 1.9,
    fontFace: H,
    fontSize: 37,
    bold: true,
    color: "FFFFFF",
    lineSpacing: 46,
    margin: 0,
  });
  s.addText(
    "Полная подборка предложений Heimstaden на Воле площадью от 50 м². Все фотографии, планировка и оснащение — в одном документе.",
    {
      isTextBox: true,
      x: 0.85,
      y: 4.05,
      w: 5.4,
      h: 1.0,
      fontFace: B,
      fontSize: 14,
      color: LIGHT,
      lineSpacing: 21,
      margin: 0,
    }
  );
  s.addText("Данные на 26 августа 2026 г.", {
    isTextBox: true,
    x: 0.85,
    y: 5.9,
    w: 5.4,
    h: 0.35,
    fontFace: B,
    fontSize: 12,
    color: MUTED,
    margin: 0,
  });
  s.addNotes(
    "Подборка собрана по каталогу oferty.heimstaden.pl. Фильтр: Варшава, район Воля, площадь от 50 м². Цены по запросу — в презентацию не включены."
  );
}

/* ---------- 2. Результат подбора ---------- */
{
  const s = pres.addSlide();
  s.background = { color: PAPER };
  kicker(s, "Результат подбора");
  slideTitle(s, "На Воле под критерий подходит одна квартира", { w: 11.9, size: 32 });

  const stats = [
    ["1", "адрес Heimstaden\nна Воле", "Grzybowska 49"],
    ["24", "квартиры\nв доме доступны", "студии и 2-комнатные"],
    ["1", "квартира\nот 50 м²", "50,99 м², 2 комнаты"],
  ];
  stats.forEach(([big, label, note], i) => {
    const x = 0.7 + i * 4.05;
    s.addShape(pres.ShapeType.roundRect, {
      x,
      y: 1.85,
      w: 3.75,
      h: 2.25,
      fill: { color: TINT },
      rectRadius: 0.12,
      line: { color: TINT },
    });
    s.addText(big, {
      isTextBox: true,
      x: x + 0.35,
      y: 2.0,
      w: 3.05,
      h: 0.95,
      fontFace: H,
      fontSize: 54,
      bold: true,
      color: ACCENT,
      margin: 0,
      valign: "middle",
    });
    s.addText(label, {
      isTextBox: true,
      x: x + 0.35,
      y: 2.95,
      w: 3.05,
      h: 0.62,
      fontFace: B,
      fontSize: 14,
      bold: true,
      color: INK,
      margin: 0,
      lineSpacing: 17,
    });
    s.addText(note, {
      isTextBox: true,
      x: x + 0.35,
      y: 3.6,
      w: 3.05,
      h: 0.34,
      fontFace: B,
      fontSize: 12,
      color: MUTED,
      margin: 0,
    });
  });

  s.addText("Как отбирали", {
    isTextBox: true,
    x: 0.7,
    y: 4.5,
    w: 5.6,
    h: 0.4,
    fontFace: B,
    fontSize: 15,
    bold: true,
    color: INK,
    margin: 0,
  });
  s.addText(
    [
      { text: "Каталог Heimstaden по Варшаве — 159 квартир", options: { bullet: true, breakLine: true } },
      { text: "Из них в районе Воля — 24 (все по адресу Grzybowska 49)", options: { bullet: true, breakLine: true } },
      { text: "Площадь от 50 м² — одна квартира, m0104", options: { bullet: true, breakLine: false } },
    ],
    {
      isTextBox: true,
      x: 0.7,
      y: 4.95,
      w: 5.9,
      h: 1.6,
      fontFace: B,
      fontSize: 13.5,
      color: INK,
      paraSpaceAfter: 7,
      margin: 0,
    }
  );

  s.addShape(pres.ShapeType.roundRect, {
    x: 7.0,
    y: 4.5,
    w: 5.6,
    h: 2.1,
    fill: { color: PAPER },
    line: { color: TINT, width: 1.5 },
    rectRadius: 0.1,
  });
  s.addText("Что ещё есть на Воле", {
    isTextBox: true,
    x: 7.35,
    y: 4.68,
    w: 5.0,
    h: 0.36,
    fontFace: B,
    fontSize: 15,
    bold: true,
    color: INK,
    margin: 0,
  });
  s.addText(
    "Остальные 23 квартиры в этом же доме — меньше по площади: 2-комнатные 40,7–41,8 м² и студии 30,3–38,9 м². Если снять ограничение «от 50 м²», подборку можно расширить.",
    {
      isTextBox: true,
      x: 7.35,
      y: 5.1,
      w: 5.0,
      h: 1.3,
      fontFace: B,
      fontSize: 12.5,
      color: MUTED,
      lineSpacing: 18,
      margin: 0,
    }
  );
  s.addNotes("159 квартир Heimstaden в Варшаве: Прага-Полудне 53, Влохы 46, Мокотув 35, Воля 24, Прага-Пулноц 1. Под критерий «Воля, от 50 м²» подходит только Grzybowska 49, кв. 0104.");
}

/* ---------- 3. Карточка объекта ---------- */
{
  const s = pres.addSlide();
  s.background = { color: PAPER };
  s.addImage({
    path: P("02.jpg"),
    x: 6.95,
    y: 0,
    w: 6.383,
    h: HT,
    sizing: { type: "cover", w: 6.383, h: HT },
  });

  kicker(s, "Объект 1 из 1");
  s.addText("50,99 м²\n2 комнаты", {
    isTextBox: true,
    x: 0.7,
    y: 0.6,
    w: 5.9,
    h: 1.4,
    fontFace: H,
    fontSize: 34,
    bold: true,
    color: INK,
    lineSpacing: 38,
    margin: 0,
  });
  s.addText("ул. Гжибовска 49, кв. 0104 · Варшава, Воля", {
    isTextBox: true,
    x: 0.7,
    y: 1.95,
    w: 5.9,
    h: 0.4,
    fontFace: B,
    fontSize: 15,
    color: MUTED,
    margin: 0,
  });

  const facts = [
    ["Площадь", "50,99 м²"],
    ["Комнаты", "Гостиная с кухней + спальня"],
    ["Этаж", "1-й, дом с лифтом"],
    ["Год постройки", "2022"],
    ["Балкон / лоджия", "Есть, 5,34 м²"],
    ["Кондиционер", "Есть"],
    ["Интернет", "Включён, до 550 Мбит/с"],
    ["Доступна", "с 26 августа 2026 г."],
  ];
  facts.forEach(([k, v], i) => {
    const y = 2.6 + i * 0.5;
    s.addText(k, {
      isTextBox: true,
      x: 0.7,
      y,
      w: 2.3,
      h: 0.42,
      fontFace: B,
      fontSize: 12.5,
      color: MUTED,
      margin: 0,
      valign: "middle",
    });
    s.addText(v, {
      isTextBox: true,
      x: 3.0,
      y,
      w: 3.6,
      h: 0.42,
      fontFace: B,
      fontSize: 13,
      bold: true,
      color: INK,
      margin: 0,
      valign: "middle",
    });
  });
  s.addNotes("Договор напрямую с собственником, без комиссии. Питомцы разрешены. Возможна регистрация (zameldowanie) по договору найма.");
}

/* ---------- 4. Планировка ---------- */
{
  const s = pres.addSlide();
  s.background = { color: TINT };
  kicker(s, "Планировка");
  slideTitle(s, "m0104 · 1-й этаж", { w: 6.0 });

  s.addShape(pres.ShapeType.rect, { x: 7.4, y: 0.45, w: 5.2, h: 6.6, fill: { color: PAPER } });
  s.addImage({ path: P("08.jpg"), x: 7.55, y: 0.6, w: 4.9, h: 6.3, sizing: { type: "contain", w: 4.9, h: 6.3 } });

  const rooms = [
    ["Прихожая и кухонная зона", "9,13 м²"],
    ["Гостиная", "23,67 м²"],
    ["Ванная комната", "7,45 м²"],
    ["Спальня", "10,72 м²"],
    ["Лоджия", "5,34 м²"],
  ];
  rooms.forEach(([name, area], i) => {
    const y = 1.75 + i * 0.78;
    numberBadge(s, i + 1, 0.7, y + 0.06);
    s.addText(name, {
      isTextBox: true,
      x: 1.32,
      y,
      w: 3.6,
      h: 0.55,
      fontFace: B,
      fontSize: 14,
      bold: true,
      color: INK,
      margin: 0,
      valign: "middle",
    });
    s.addText(area, {
      isTextBox: true,
      x: 5.0,
      y,
      w: 1.6,
      h: 0.55,
      fontFace: B,
      fontSize: 14,
      color: MUTED,
      align: "right",
      margin: 0,
      valign: "middle",
    });
  });

  s.addText(
    "Нумерация соответствует плану справа. Кухня открыта в гостиную, спальня изолированная, со встроенным шкафом. Размеры на плане ориентировочные.",
    {
      isTextBox: true,
      x: 0.7,
      y: 5.85,
      w: 5.9,
      h: 1.0,
      fontFace: B,
      fontSize: 12,
      color: MUTED,
      lineSpacing: 17,
      margin: 0,
    }
  );
}

/* ---------- 5–11. Фотогалерея ---------- */
photoSlide("02.jpg", "Гостиная", "23,67 м², большие окна в пол, выход на лоджию");
photoSlide("03.jpg", "Гостиная и обеденная зона", "Справа — вход в изолированную спальню");
photoSlide("01.jpg", "Кухня, открытая в гостиную", "Индукционная плита, духовка, вытяжка, посудомоечная машина, холодильник");

/* два фото на одном слайде */
{
  const s = pres.addSlide();
  s.background = { color: PAPER };
  kicker(s, "Фотогалерея");
  slideTitle(s, "Спальня и ванная комната", { w: 11.9 });

  s.addImage({ path: P("04.jpg"), x: 0.7, y: 1.65, w: 5.9, h: 3.95, sizing: { type: "cover", w: 5.9, h: 3.95 } });
  s.addText("Спальня · 10,72 м²", {
    isTextBox: true,
    x: 0.7,
    y: 5.72,
    w: 5.9,
    h: 0.34,
    fontFace: B,
    fontSize: 13.5,
    bold: true,
    color: INK,
    margin: 0,
  });
  s.addText("Кровать 160 × 200 см, встроенный шкаф, прикроватные тумбы", {
    isTextBox: true,
    x: 0.7,
    y: 6.06,
    w: 5.9,
    h: 0.5,
    fontFace: B,
    fontSize: 12,
    color: MUTED,
    margin: 0,
  });

  s.addImage({ path: P("06.jpg"), x: 6.95, y: 1.65, w: 5.68, h: 3.95, sizing: { type: "cover", w: 5.68, h: 3.95 } });
  s.addText("Ванная комната · 7,45 м²", {
    isTextBox: true,
    x: 6.95,
    y: 5.72,
    w: 5.68,
    h: 0.34,
    fontFace: B,
    fontSize: 13.5,
    bold: true,
    color: INK,
    margin: 0,
  });
  s.addText("Ванна, раковина с тумбой, стиральная машина, полотенцесушитель", {
    isTextBox: true,
    x: 6.95,
    y: 6.06,
    w: 5.68,
    h: 0.5,
    fontFace: B,
    fontSize: 12,
    color: MUTED,
    margin: 0,
  });
}

photoSlide("05.jpg", "Прихожая и кухонный блок", "Встроенные шкафы, видеодомофон, кондиционер");
photoSlide("07.jpg", "Grzybowska 49", "Дом 2022 года: ресепшн, круглосуточная охрана, велопарковка, зелёный внутренний двор");

/* ---------- 12. Оснащение ---------- */
{
  const s = pres.addSlide();
  s.background = { color: PAPER };
  kicker(s, "Оснащение");
  slideTitle(s, "Квартира сдаётся полностью меблированной", { w: 11.9, size: 32 });

  const groups = [
    ["Кухня", "Индукционная плита, духовка, вытяжка, посудомоечная машина, холодильник с морозильной камерой, обеденный стол со стульями"],
    ["Гостиная", "Диван, тумба под ТВ, встроенные шкафы, окна в пол с выходом на лоджию"],
    ["Спальня", "Кровать 160 × 200 см с матрасом, шкаф, прикроватные тумбы"],
    ["Ванная", "Ванна, раковина с тумбой, стиральная машина, полотенцесушитель"],
    ["В квартире", "Кондиционер, интернет до 550 Мбит/с в стоимости аренды"],
    ["В доме", "Лифт, ресепшн, круглосуточная охрана, велопарковка, подземный гараж (по запросу)"],
  ];
  groups.forEach(([title, body], i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.7 + col * 6.25;
    const y = 1.75 + row * 1.75;
    s.addShape(pres.ShapeType.roundRect, {
      x,
      y,
      w: 5.95,
      h: 1.5,
      fill: { color: TINT },
      line: { color: TINT },
      rectRadius: 0.1,
    });
    numberBadge(s, i + 1, x + 0.3, y + 0.28);
    s.addText(title, {
      isTextBox: true,
      x: x + 0.85,
      y: y + 0.24,
      w: 4.8,
      h: 0.36,
      fontFace: B,
      fontSize: 14.5,
      bold: true,
      color: INK,
      margin: 0,
      valign: "middle",
    });
    s.addText(body, {
      isTextBox: true,
      x: x + 0.85,
      y: y + 0.62,
      w: 4.8,
      h: 0.75,
      fontFace: B,
      fontSize: 11.5,
      color: MUTED,
      lineSpacing: 15,
      margin: 0,
    });
  });
}

/* ---------- 13. Локация ---------- */
{
  const s = pres.addSlide();
  s.background = { color: PAPER };
  s.addImage({
    path: P("03.jpg"),
    x: 0,
    y: 0,
    w: 5.6,
    h: HT,
    sizing: { type: "cover", w: 5.6, h: HT },
  });

  kicker(s, "Локация", { x: 6.2, y: 0.66, w: 6.4 });
  s.addText("Историческая Воля", {
    isTextBox: true,
    x: 6.2,
    y: 1.1,
    w: 6.4,
    h: 0.8,
    fontFace: H,
    fontSize: 32,
    bold: true,
    color: INK,
    margin: 0,
    valign: "middle",
  });
  s.addText("Между Browary Warszawskie и Fabryka Norblina, в окружении новых офисных кварталов", {
    isTextBox: true,
    x: 6.2,
    y: 1.95,
    w: 6.4,
    h: 0.6,
    fontFace: B,
    fontSize: 13.5,
    color: MUTED,
    lineSpacing: 19,
    margin: 0,
  });

  const points = [
    ["Метро Rondo Daszyńskiego", "линия M2, несколько минут пешком"],
    ["Browary Warszawskie", "рестораны, магазины, площадь с фонтанами"],
    ["Fabryka Norblina", "кинотеатр, фудкорт, рынок и музей"],
    ["Деловой центр Воли", "Warsaw Unit, Skyliner, Generation Park"],
    ["Центр города", "Дворец культуры — около 2 км"],
  ];
  points.forEach(([title, body], i) => {
    const y = 2.85 + i * 0.82;
    numberBadge(s, i + 1, 6.2, y + 0.02);
    s.addText(title, {
      isTextBox: true,
      x: 6.82,
      y,
      w: 5.8,
      h: 0.38,
      fontFace: B,
      fontSize: 14,
      bold: true,
      color: INK,
      margin: 0,
      valign: "middle",
    });
    s.addText(body, {
      isTextBox: true,
      x: 6.82,
      y: y + 0.36,
      w: 5.8,
      h: 0.32,
      fontFace: B,
      fontSize: 12,
      color: MUTED,
      margin: 0,
      valign: "middle",
    });
  });
}

/* ---------- 14. Итог / контакты ---------- */
{
  const s = pres.addSlide();
  s.background = { color: INK };
  s.addImage({
    path: P("01.jpg"),
    x: 7.5,
    y: 0,
    w: 5.833,
    h: HT,
    sizing: { type: "cover", w: 5.833, h: HT },
  });

  s.addText("ИТОГ", {
    isTextBox: true,
    x: 0.85,
    y: 1.0,
    w: 6.0,
    h: 0.35,
    fontFace: B,
    fontSize: 12,
    bold: true,
    charSpacing: 2.6,
    color: ACCENT,
    margin: 0,
  });
  s.addText("Grzybowska 49 · кв. 0104", {
    isTextBox: true,
    x: 0.85,
    y: 1.5,
    w: 6.35,
    h: 0.8,
    fontFace: H,
    fontSize: 28,
    bold: true,
    color: "FFFFFF",
    margin: 0,
    valign: "middle",
  });
  s.addText(
    "Единственная квартира Heimstaden на Воле от 50 м²: двухкомнатная, 50,99 м², с лоджией и кондиционером, свободна с 26 августа 2026 года.",
    {
      isTextBox: true,
      x: 0.85,
      y: 2.5,
      w: 5.9,
      h: 1.2,
      fontFace: B,
      fontSize: 14,
      color: LIGHT,
      lineSpacing: 21,
      margin: 0,
    }
  );

  const links = [
    ["Объявление", "oferty.heimstaden.pl · № 42216"],
    ["3D-тур", "my.matterport.com/show/?m=QdbufVrYA3d"],
    ["Телефон", "+48 884 204 735"],
    ["Почта", "witaj@heimstaden.pl"],
  ];
  links.forEach(([k, v], i) => {
    const y = 4.0 + i * 0.62;
    s.addText(k, {
      isTextBox: true,
      x: 0.85,
      y,
      w: 1.75,
      h: 0.4,
      fontFace: B,
      fontSize: 12,
      color: MUTED,
      margin: 0,
      valign: "middle",
    });
    s.addText(v, {
      isTextBox: true,
      x: 2.6,
      y,
      w: 4.6,
      h: 0.4,
      fontFace: B,
      fontSize: 12.5,
      bold: true,
      color: "FFFFFF",
      margin: 0,
      valign: "middle",
    });
  });

  s.addText("Аренда напрямую от собственника, без комиссии · Питомцы разрешены · Данные и наличие — на 26.08.2026", {
    isTextBox: true,
    x: 0.85,
    y: 6.6,
    w: 6.2,
    h: 0.5,
    fontFace: B,
    fontSize: 10.5,
    color: MUTED,
    lineSpacing: 14,
    margin: 0,
  });
  s.addNotes("Ссылка на объявление: https://oferty.heimstaden.pl/warszawa/offers/42216-2-pokojowe-5099-m2-balkon-internet-w-cenie-bezposrednio");
}

pres.writeFile({ fileName: path.join(__dirname, "Kvartiry-50m2-Wola-Heimstaden.pptx") }).then((f) => {
  console.log("written:", f);
});
