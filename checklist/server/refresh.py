#!/usr/bin/env python3
"""Положить свежесобранный документ в сервер и включить в нём общий режим.

Страница одна и та же в двух видах: скачанный файл работает сам по себе, а тот,
что отдаёт сервер, объявляет о себе одной строкой — по ней клиент понимает, что
ответы общие. Разделение сделано здесь, а не в сборщике, чтобы файл для
скачивания не знал ни про какой сервер.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "Chto-menyat-na-sayte.html")
DST = os.path.join(HERE, "public", "index.html")
MARK = '<script>window.LPB_API="/api";</script>'

page = open(SRC, encoding="utf-8").read()
if MARK not in page:
    page = page.replace('<div class="sheet">', MARK + '\n<div class="sheet">', 1)
os.makedirs(os.path.dirname(DST), exist_ok=True)
open(DST, "w", encoding="utf-8").write(page)
print(f"{DST}  {round(len(page.encode()) / 1024)} КБ")
