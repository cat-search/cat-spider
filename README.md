# Overview

Проект для импорта данных из БД ВК

# Tasks

Tasks:
- import_sites:  Импорт сайтов из БД ВК в векторную БД.
- import_pages:  Импорт страниц сайтов из БД ВК в векторную БД.
- fetch_files:   Скачивание файлов на локальную файловую систему.
- import_files:  Парсинг скачанных файлов и импорт текста в векторную БД.

# Структура

```text
.
├── doc                             # Документация
├── src
│   ├── common                      # Общие утилиты и модули
│   │   ├── db.py                   # Работа с Postgresql
│   │   ├── log.py                  # Логирование
│   │   ├── mongo.py                # Работа с MongoDB
│   │   ├── settings.py             # Настройки проекта
│   │   ├── utils.py                # Общие утилиты
│   │   └── vectordb.py             # Работа с векторными БД
│   ├── migrations                  # папка Alembic 
│   │   ├── versions                # Миграции БД postgresql
│   │   ├── env.py                  # Alembic configuration
│   │   └── script.py.mako          # 
│   ├── models                      # Модели sqlalchemy для postgresql
│   │   ├── base.py                 # Базовые модели
│   │   ├── cat_meta.py             # Модели нашей БД catsearch
│   │   ├── vk_cms.py               # Модели БД VK cms
│   │   ├── vk_filestorage.py       # Модели БД VK filestorage 
│   │   └── vk_lists.py             # Модели БД VK lists
│   ├── notebook                    # Jupyter notebooks
│   └── tasks                       # Основный таски, выполняющие импорт 
├── alembic.ini                     # Alembic configuration
├── poetry.lock                     # poetry
├── pyproject.toml                  # poetry
└── README.md                       # Основной ридми парсера

```

New text



# Запросы данных

## 1. Get sites

Список id сайтов, которые нам нужны и поля:

```sql
select
    ss.id
    , ss.name
    , ss.created_by_id
    , ss.created_at
    , ss.updated_by_id
    , ss.updated_at
from sites_site ss
where ss.name in (
    'People hub инструкции',
    'People hub архитектура',
    'Информация о хакатоне',
    'Работы Фролова',
    'Музеи',
    'Литература',
    'Таблицы'
)
-- +------------------------------------+----------------------+------------------------------------+---------------------------------+------------------------------------+---------------------------------+
-- |id                                  |name                  |created_by_id                       |created_at                       |updated_by_id                       |updated_at                       |
-- +------------------------------------+----------------------+------------------------------------+---------------------------------+------------------------------------+---------------------------------+
-- |83f29091-def2-42a4-82c4-453103d8a457|Информация о хакатоне |f60d1f0a-62d6-4e0e-8163-965fa8fe48a7|2025-03-28 10:39:20.341992 +00:00|f60d1f0a-62d6-4e0e-8163-965fa8fe48a7|2025-03-28 10:48:25.923636 +00:00|
-- |3d2d628c-0b80-470d-a9fc-f19b353971b7|Литература            |f60d1f0a-62d6-4e0e-8163-965fa8fe48a7|2025-03-28 11:10:14.346940 +00:00|f60d1f0a-62d6-4e0e-8163-965fa8fe48a7|2025-03-28 11:13:38.998593 +00:00|
-- |b7a8428a-9f61-46ff-9fcf-f835a577e1e3|People hub инструкции |f60d1f0a-62d6-4e0e-8163-965fa8fe48a7|2025-03-28 10:03:09.440838 +00:00|f60d1f0a-62d6-4e0e-8163-965fa8fe48a7|2025-03-28 10:28:46.999945 +00:00|
-- |023540f1-15d1-411d-b2c5-3d596089654b|People hub архитектура|f60d1f0a-62d6-4e0e-8163-965fa8fe48a7|2025-03-28 10:29:06.152421 +00:00|f60d1f0a-62d6-4e0e-8163-965fa8fe48a7|2025-03-28 10:38:02.939622 +00:00|
-- |0f11f06b-1c6c-41a8-b30b-1061ce626391|Таблицы               |f60d1f0a-62d6-4e0e-8163-965fa8fe48a7|2025-03-28 11:14:08.996371 +00:00|f60d1f0a-62d6-4e0e-8163-965fa8fe48a7|2025-03-28 11:22:32.680268 +00:00|
-- |6d111c1d-5d0f-406c-a1e1-74fb2a8acc1d|Работы Фролова        |f60d1f0a-62d6-4e0e-8163-965fa8fe48a7|2025-03-28 10:48:58.947155 +00:00|f60d1f0a-62d6-4e0e-8163-965fa8fe48a7|2025-03-28 10:52:05.958946 +00:00|
-- |3b508b32-4c04-4a22-bc4f-94e4bd9f0bdb|Музеи                 |f60d1f0a-62d6-4e0e-8163-965fa8fe48a7|2025-03-28 11:03:57.383200 +00:00|f60d1f0a-62d6-4e0e-8163-965fa8fe48a7|2025-03-28 11:08:18.939565 +00:00|
-- +------------------------------------+----------------------+------------------------------------+---------------------------------+------------------------------------+---------------------------------+
```

Эти сайты не имеют подчиненных, потому что:

```sql
select count(*) from sites_site as ss where ss.parent_id in (
    '83f29091-def2-42a4-82c4-453103d8a457',
    '3d2d628c-0b80-470d-a9fc-f19b353971b7',
    'b7a8428a-9f61-46ff-9fcf-f835a577e1e3',
    '023540f1-15d1-411d-b2c5-3d596089654b',
    '0f11f06b-1c6c-41a8-b30b-1061ce626391',
    '6d111c1d-5d0f-406c-a1e1-74fb2a8acc1d',
    '3b508b32-4c04-4a22-bc4f-94e4bd9f0bdb'
);
-- 0
```

## 2. Get site objects

### Get pages

Страницы нужных нам сайтов:

```sql
SELECT
    pp.id,
    pp.name,
    pp.body,            -- содержимое страницы
    pp.views_count,     -- Кол-во просмотров
    -- pp.status,       -- все published
    -- pp.is_main,         -- ???
    -- pp.settings,
    pp.created_at,
    pp.created_by_id,
    pp.updated_at,
    pp.updated_by_id,
    -- pp.parent_id,    -- all null
    sso.id,
    sso.site_id,
    sso.name,           -- Название объекта
    sso.type            -- page all
FROM cms.public.pages_page AS pp
LEFT JOIN sites_serviceobject AS sso ON sso.external_id = pp.id::TEXT
WHERE sso.site_id in (
    '83f29091-def2-42a4-82c4-453103d8a457',
    '3d2d628c-0b80-470d-a9fc-f19b353971b7',
    'b7a8428a-9f61-46ff-9fcf-f835a577e1e3',
    '023540f1-15d1-411d-b2c5-3d596089654b',
    '0f11f06b-1c6c-41a8-b30b-1061ce626391',
    '6d111c1d-5d0f-406c-a1e1-74fb2a8acc1d',
    '3b508b32-4c04-4a22-bc4f-94e4bd9f0bdb'
);
```

### Get file links from sites

Все файли с линками для нужных нам сайтов.

```sql
SELECT
--     so.*,
    so.id,                  -- storage object id
    so.name,                -- filename
    -- so.type,
    so.context_folder_id,   -- папка, определяющая контекст (например, Blog_{id}).
    so.created_at,
    so.created_by_id,
    so.updated_at,
    so.updated_by_id,
    so.site_id,
    sv.size,                -- file size
    sv.link                 -- download link
FROM filestorage.public.storage_storageobject AS so
JOIN filestorage.public.storage_version AS sv
    ON sv.id = so.version_id
WHERE so.site_id in (
    '83f29091-def2-42a4-82c4-453103d8a457',
    '3d2d628c-0b80-470d-a9fc-f19b353971b7',
    'b7a8428a-9f61-46ff-9fcf-f835a577e1e3',
    '023540f1-15d1-411d-b2c5-3d596089654b',
    '0f11f06b-1c6c-41a8-b30b-1061ce626391',
    '6d111c1d-5d0f-406c-a1e1-74fb2a8acc1d',
    '3b508b32-4c04-4a22-bc4f-94e4bd9f0bdb'
)
    AND so.type = 1 -- file;
-- +------------------------------------+-------------------------------------------------------------------+------------------------------------+---------------------------------+-------------+---------------------------------+-------------+------------------------------------+---------+------------------------------------------------------------------------------------------------------------------+
-- |id                                  |name                                                               |context_folder_id                   |created_at                       |created_by_id|updated_at                       |updated_by_id|site_id                             |size     |link                                                                                                              |
-- +------------------------------------+-------------------------------------------------------------------+------------------------------------+---------------------------------+-------------+---------------------------------+-------------+------------------------------------+---------+------------------------------------------------------------------------------------------------------------------+
-- |231e99d5-150d-430f-a80a-05593ef3722e|Фролов_К_В_Горные_машины_МЭ,_том_IV_24_2010.pdf                    |61d09f6f-172e-49d0-b608-fe06e61d8d93|2025-03-28 10:50:36.386742 +00:00|74           |2025-03-28 10:50:36.971911 +00:00|74           |6d111c1d-5d0f-406c-a1e1-74fb2a8acc1d|36932783 |attachments/7aa333f8-0bc2-11f0-96fd-1e065ec9454b/Фролов_К_В_Горные_машины_МЭ_том_IV_24_2010.pdf                   |
-- |9c0cb7b3-9d6e-4a84-8230-38dbbdd6293d|Фролов_К_В_Динамика_и_прочность_машин_МЭ,_том_I_3,_книга_1_1994.pdf|61d09f6f-172e-49d0-b608-fe06e61d8d93|2025-03-28 10:49:58.644665 +00:00|74           |2025-03-28 10:50:05.927554 +00:00|74           |6d111c1d-5d0f-406c-a1e1-74fb2a8acc1d|26853756 |attachments/63fd8784-0bc2-11f0-8632-1e065ec9454b/Фролов_К_В_Динамика_и_прочность_машин_МЭ_том_I_3_книга_1_1994.pdf|
-- |4dc82ffa-c9d2-4a41-8a44-698d38d5d585|Фролов_К_В_Двигатели_внутреннего_сгорания_МЭ,_том_IV_14_2013.pdf   |61d09f6f-172e-49d0-b608-fe06e61d8d93|2025-03-28 10:50:20.514173 +00:00|74           |2025-03-28 10:50:21.667745 +00:00|74           |6d111c1d-5d0f-406c-a1e1-74fb2a8acc1d|38139085 |attachments/710267b0-0bc2-11f0-96fd-1e065ec9454b/Фролов_К_В_Двигатели_внутреннего_сгорания_МЭ_том_IV_14_2013.pdf  |
-- |5d262875-accf-4e06-9bb3-6fc6cd891725|Фролов_К_В_Авиационные_двигатели_МЭ,_том_IV_21,_книга_3_2010.pdf   |61d09f6f-172e-49d0-b608-fe06e61d8d93|2025-03-28 10:51:56.769460 +00:00|74           |2025-03-28 10:51:57.875185 +00:00|74           |6d111c1d-5d0f-406c-a1e1-74fb2a8acc1d|74928667 |attachments/a99f0628-0bc2-11f0-9458-1e065ec9454b/Фролов_К_В_Авиационные_двигатели_МЭ_том_IV_21_книга_3_2010.pdf   |
-- |b934a360-fb15-4b4b-b05e-c6352a3feca3|04_Великие_музеи_мира_Египетский_музей_2011.pdf                  |a72771ed-4bd3-4e85-83e1-3f8a5b4dcc48|2025-03-28 11:05:51.923164 +00:00|74           |2025-03-28 11:05:54.271063 +00:00|74           |3b508b32-4c04-4a22-bc4f-94e4bd9f0bdb|65950480 |attachments/9c290c6c-0bc4-11f0-b39a-1e065ec9454b/04_Великие_музеи_мира_Египетский_музей_2011.pdf                  |
-- |fc6ba7f2-a0d7-4cab-ad26-4b19daba8752|03_Великие_музеи_мира_Лувр_Париж_2011.pdf                          |a72771ed-4bd3-4e85-83e1-3f8a5b4dcc48|2025-03-28 11:06:43.050250 +00:00|74           |2025-03-28 11:06:45.034270 +00:00|74           |3b508b32-4c04-4a22-bc4f-94e4bd9f0bdb|165373205|attachments/b9d0cb9c-0bc4-11f0-b39a-1e065ec9454b/03_Великие_музеи_мира_Лувр_Париж_2011.pdf                        |
-- |c86b5b0e-0425-4c3d-a9b5-71c75f855f75|02_Великие_музеи_мира_Прадо_Мадрид_2011.pdf                        |a72771ed-4bd3-4e85-83e1-3f8a5b4dcc48|2025-03-28 11:07:47.023565 +00:00|74           |2025-03-28 11:07:48.983443 +00:00|74           |3b508b32-4c04-4a22-bc4f-94e4bd9f0bdb|173441090|attachments/dfa9f726-0bc4-11f0-8d6f-1e065ec9454b/02_Великие_музеи_мира_Прадо_Мадрид_2011.pdf                      |
-- |2dd6f608-97ca-4d64-a093-dd14a36fb39e|Хладнокровное-убийство.doc                                        |fb4f5fdb-321a-4ed6-a994-30a27953014d|2025-03-28 11:13:04.592737 +00:00|74           |2025-03-28 11:13:05.881588 +00:00|74           |3d2d628c-0b80-470d-a9fc-f19b353971b7|2122752  |attachments/9e5cfb6e-0bc5-11f0-9532-1e065ec9454b/Хладнокровное-убийство.doc                                       |
-- |fab066dc-90ee-495a-a2f1-76a7d709b459|Улисс.doc                                                          |fb4f5fdb-321a-4ed6-a994-30a27953014d|2025-03-28 11:13:15.492729 +00:00|74           |2025-03-28 11:13:16.486255 +00:00|74           |3d2d628c-0b80-470d-a9fc-f19b353971b7|7355904  |attachments/a4c0cf1c-0bc5-11f0-958f-1e065ec9454b/Улисс.doc                                                        |
-- +------------------------------------+-------------------------------------------------------------------+------------------------------------+---------------------------------+-------------+---------------------------------+-------------+------------------------------------+---------+------------------------------------------------------------------------------------------------------------------+

```

## Download files

## Parse files


## Dima's research

```sql
with sites as (
select ss.* from sites_site ss
 inner join (
 select name from (
  values 
   ('People hub инструкции'),
   ('People hub архитектура'),
   ('Информация о Хакатоне'),
   ('Работы Фролова'),
   ('Музеи'),
   ('Литература'),
   ('Таблицы')
 ) as site_names(name) 
 ) as sn on lower(ss."name") = lower(sn."name")
),
files as (
 select s.id as s_id, s."name" as s_name, so."name" as so_name, so.id as so_id, sv.version_number, 'https://hackaton.hb.ru-msk.vkcloud-storage.ru/media/' || link as link
  from sites s 
  left join storage_storageobject so on so.site_id = s.id and so.type = 1
  left join storage_version sv on sv.storage_object_id = so.id
),
pages as (
 select s.id as s_id, pp."name" as page_name, pp.slug, pp.id as pp_id, pp.parent_id
  from sites s
  inner join sites_serviceobject so on so.site_id = s.id
  inner join pages_page pp on pp.id::text = so.external_id 
),
service_objects as (
select s.id as s_id, so."name" as so_name, so.external_id 
 from sites_serviceobject so 
 inner join sites s on so.site_id = s.id
where so.type in ('page', 'filestorage', 'list')
)
```
