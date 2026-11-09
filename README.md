# news-parser

CLI-парсер RSS/Atom-лент на Python. Собирает новости из одного или нескольких
источников, чистит HTML, фильтрует по ключевому слову и выгружает в CSV или JSON.

## Возможности

- Один или несколько источников (`--feed` можно повторять).
- Поддержка RSS и Atom (через `feedparser`).
- Очистка HTML из заголовков и описаний.
- Нормализация даты в ISO 8601.
- Дедупликация по ссылке.
- Фильтр по ключевому слову (заголовок + описание).
- Экспорт в CSV или JSON.
- Устойчивость к ошибкам: недоступный фид пропускается, остальные собираются.

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Использование

Собрать 10 свежих новостей с Хабра в CSV:

```bash
python news_parser.py -f "https://habr.com/ru/rss/news/?fl=ru" -n 10
```

Несколько источников + фильтр + JSON:

```bash
python news_parser.py \
  -f "https://lenta.ru/rss/news" \
  -f "https://techcrunch.com/feed/" \
  -k "nvidia" \
  -F json \
  -o output/nvidia.json
```

### Параметры

| Флаг | Описание | По умолчанию |
| --- | --- | --- |
| `-f, --feed` | URL фида (можно повторять) | обязательный |
| `-n, --limit` | Максимум статей с одного фида | `20` |
| `-k, --keyword` | Фильтр по ключевому слову | — |
| `-F, --format` | `csv` или `json` | `csv` |
| `-o, --out` | Путь к файлу результата | `output/news_<дата>.<формат>` |
| `--timeout` | Таймаут запроса, сек | `15` |

## Формат данных

Каждая статья: `title`, `link`, `published` (ISO 8601), `summary`, `source`.

## Тесты

```bash
python -m unittest discover -s tests -t . -v
```

## Структура

```
news_parser.py     логика парсинга + CLI
tests/             unit-тесты (без сети, на встроенном фиде)
requirements.txt   зависимости
```
