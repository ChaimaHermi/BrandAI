import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Ajouter le dossier backend-api/ au path
# Pour que "from app.core.config import settings" fonctionne
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer settings pour lire DATABASE_URL depuis .env
from app.core.config import settings

# Importer Base + tous les modèles
# OBLIGATOIRE : Alembic doit connaître les modèles pour les migrations
from app.core.database import Base
import app.models.user  # noqa
import app.models.idea  # noqa
import app.models.market_analysis  # noqa

config = context.config

# Override DATABASE_URL avec celle du .env
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# C'est ici qu'Alembic lit tes modèles pour détecter les changements
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()