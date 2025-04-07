from enum import Enum

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Integer,
)
from sqlalchemy.dialects.postgresql import (
    UUID,
    JSONB,
    TSVECTOR,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from src.models.base import ModelBase

Base = declarative_base()


class Site(ModelBase, Base):
    """
    Представляет собой структуру для хранения информации о сайте внутри системы.
    Может быть как самостоятельным сайтом, так и вложенным (дочерним сайтом или разделом).

    - Иерархия: сайты могут быть вложенными, строя древовидные структуры.
    - Гибкие связи: через ServiceObject и Page можно связать с контентом, меню и т.п.
    """
    __tablename__ = 'sites_site'
    __table_args__ = (
        {
            'schema': 'public',
            'info': {'skip_autogenerate': True},  # Skip in alembic migrations
        },
    )

    # Уникальный идентификатор сайта, генерируется автоматически
    id                          = Column(UUID(as_uuid=True), primary_key=True)
    # Уникальное название сайта. Обязательное.
    name                        = Column(String(150), nullable=False)
    # Описание сайта. Необязательное текстовое поле
    description                 = Column(String(1500), nullable=False)
    # Уникальный slug (человеко-читаемый идентификатор), используется, например, в URL
    slug                        = Column(String(50), nullable=False)
    # Статус сайта (enum)
    status                      = Column(String(20), nullable=False)
    # Показывается ли сайт в навигации
    is_navigation_visible       = Column(Boolean, nullable=False)
    created_at                  = Column(DateTime(timezone=True))
    updated_at                  = Column(DateTime(timezone=True))

    # Foreign keys
    filestorage_root_folder_id  = Column(UUID(as_uuid=True))
    # FK на родительский сайт (ON DELETE SET NULL)
    parent_id                   = Column(UUID(as_uuid=True))
    # FK на пользователя, создавшего сайт
    created_by_id               = Column(UUID(as_uuid=True))
    # FK на пользователя, который последним редактировал сайт.
    updated_by_id               = Column(UUID(as_uuid=True))


class SiteStatus(str, Enum):
    """
    Статус сайта (enum)
    """
    draft = "draft"
    published = "published"
    archived = "archived"


class Page(Base):
    """
    Представляет сущность страницы, используемую для хранения контента, метаданных, связей и полнотекстового поиска.

    ВАЖНО:
    Принадлежность страницы к сайту определяется через таблицу `sites_serviceobject`, где:

    - `ServiceObject.external_id` = `id страницы`
    - `ServiceObject.site_id` = `id сайта`

    Пример SQL-запроса: найти страницы сайта с `id = 45f1ce96-405a-439a-ad12-92e381e34835`

    ```sql
    SELECT *
    FROM pages_page AS pp
    LEFT JOIN sites_serviceobject AS sso ON sso.external_id = pp.id::TEXT
    WHERE sso.site_id = '45f1ce96-405a-439a-ad12-92e381e34835';
    ```
    """
    __tablename__ = 'pages_page'
    __table_args__ = (
        {
            'schema': 'public',
            'info': {'skip_autogenerate': True},  # Skip in alembic migrations

        }
    )

    # Первичный ключ
    id = Column(UUID(as_uuid=True), primary_key=True)
    # Название страницы
    name = Column(Text, nullable=False)
    # Слаг URL (уникальный)
    slug = Column(Text, nullable=False)
    # Контент страницы
    body = Column(JSON)
    # Кол-во просмотров
    views_count = Column(Integer, nullable=False)
    # Статус публикации (enum)
    status = Column(String(20))
    # Основная страница сайта
    is_main = Column(Boolean, nullable=False)

    # Настройки отображения страницы
    settings = Column(
        JSONB,
        nullable=False,
        server_default='{"is_reacted": true, "is_comments": true, "is_views_count": true, '
                       '"is_created_at_visible": true, "is_created_by_visible": true, '
                       '"is_updated_at_visible": true, "is_updated_by_visible": true}'
    )

    # Дата создания
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # Пользователь-создатель
    created_by_id = Column(UUID(as_uuid=True), ForeignKey('public.users.keycloak_id', ondelete='CASCADE'))
    # Дата обновления
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Последний редактор
    updated_by_id = Column(UUID(as_uuid=True), ForeignKey('public.users.keycloak_id', ondelete='CASCADE'))
    # FK на родительскую страницу
    parent_id = Column(UUID(as_uuid=True), ForeignKey('public.pages_page.id', ondelete='SET NULL'))
    # Generated columns (PostgreSQL specific)
    ts_vector_name = Column(
        TSVECTOR,
        nullable=False,
        server_default=func.to_tsvector('simple', 'name'),
        # persisted=True
    )
    ts_vector_body = Column(
        TSVECTOR,
        nullable=False,
        server_default=func.to_tsvector(
            'simple',
            func.coalesce(func.json_extract_path_text(body, 'data'), '')
        ),
        # persisted=True
    )
