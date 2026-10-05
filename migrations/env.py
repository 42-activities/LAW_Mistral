from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import get_settings
from app.db import Base

# Import model modules so their tables register on Base.metadata.
from app.modules.core import models as _core_models  # noqa: F401
from app.modules.core import reference as _core_reference  # noqa: F401
from app.modules.llm import models as _llm_models  # noqa: F401
from app.modules.recommender import models as _recommender_models  # noqa: F401
from app.modules.risk import models as _risk_models  # noqa: F401
from app.modules.saas import models as _saas_models  # noqa: F401
from app.modules.source import models as _source_models  # noqa: F401
from app.modules.tax import models as _tax_models  # noqa: F401
from app.modules.treaty import models as _treaty_models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata


def run_migrations_online() -> None:
    # Tests pass their own connection to migrate a second database (tests/conftest.py).
    given = config.attributes.get("connection")
    if given is not None:
        context.configure(connection=given, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
        return
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
