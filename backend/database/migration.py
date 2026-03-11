from sqlalchemy import inspect, text

from .connection import engine, SessionLocal
from .session import session_lock
from utils.logging import logger


def _get_inspector():
    return inspect(engine)


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _column_names(inspector, table_name: str) -> set[str]:
    if not _has_table(inspector, table_name):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _unique_constraints(inspector, table_name: str) -> list[dict]:
    if not _has_table(inspector, table_name):
        return []
    return inspector.get_unique_constraints(table_name)


def _index_names(inspector, table_name: str) -> set[str]:
    if not _has_table(inspector, table_name):
        return set()
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _foreign_key_names(inspector, table_name: str) -> set[str]:
    if not _has_table(inspector, table_name):
        return set()
    return {fk["name"] for fk in inspector.get_foreign_keys(table_name) if fk.get("name")}


def _single_user_id(db) -> int | None:
    user_ids = [row[0] for row in db.execute(text("SELECT id FROM users ORDER BY id")).fetchall()]
    if len(user_ids) == 1:
        return user_ids[0]
    return None


def _ensure_prompts_table(db, dialect: str, inspector):
    if _has_table(inspector, "prompts"):
        return

    logger.info("Creating prompts table for existing database")
    if dialect == "sqlite":
        db.execute(text("""
            CREATE TABLE prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                order_index INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        """))
    else:
        db.execute(text("""
            CREATE TABLE prompts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                project_id INT NOT NULL,
                text TEXT NOT NULL,
                order_index INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_prompts_project_id FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """))


def _ensure_recordings_prompt_id(db, dialect: str, inspector):
    columns = _column_names(inspector, "recordings")
    if not columns or "prompt_id" in columns:
        return

    logger.info("Adding prompt_id column to recordings table")
    if dialect == "sqlite":
        db.execute(text("ALTER TABLE recordings ADD COLUMN prompt_id INTEGER"))
    else:
        db.execute(text("ALTER TABLE recordings ADD COLUMN prompt_id INT"))


def _ensure_projects_is_rtl(db, dialect: str, inspector):
    columns = _column_names(inspector, "projects")
    if not columns or "is_rtl" in columns:
        return

    logger.info("Adding is_rtl column to projects table")
    if dialect == "sqlite":
        db.execute(text("ALTER TABLE projects ADD COLUMN is_rtl INTEGER DEFAULT 0"))
    else:
        db.execute(text("ALTER TABLE projects ADD COLUMN is_rtl INT DEFAULT 0"))


def _sqlite_projects_need_rebuild(inspector) -> bool:
    columns = _column_names(inspector, "projects")
    if not columns:
        return False
    if "user_id" not in columns:
        return True
    for constraint in _unique_constraints(inspector, "projects"):
        if constraint.get("column_names") == ["name"]:
            return True
    return False


def _sqlite_settings_need_rebuild(inspector) -> bool:
    columns = _column_names(inspector, "settings")
    if not columns:
        return False
    if "user_id" not in columns:
        return True
    for constraint in _unique_constraints(inspector, "settings"):
        if constraint.get("column_names") == ["key"]:
            return True
    return False


def _rebuild_sqlite_projects(db, inspector):
    logger.info("Rebuilding SQLite projects table for per-user ownership")
    columns = _column_names(inspector, "projects")
    owner_id = _single_user_id(db)
    user_id_expr = "user_id" if "user_id" in columns else "NULL"
    is_rtl_expr = "is_rtl" if "is_rtl" in columns else "0"

    db.execute(text("""
        CREATE TABLE projects_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name VARCHAR(255) NOT NULL,
            is_rtl INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_projects_user_name UNIQUE (user_id, name),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """))
    db.execute(text(f"""
        INSERT INTO projects_new (id, user_id, name, is_rtl, created_at)
        SELECT
            id,
            COALESCE({user_id_expr}, :owner_id),
            name,
            COALESCE({is_rtl_expr}, 0),
            created_at
        FROM projects
    """), {"owner_id": owner_id})
    db.execute(text("DROP TABLE projects"))
    db.execute(text("ALTER TABLE projects_new RENAME TO projects"))
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects (user_id)"))
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_projects_name ON projects (name)"))


def _rebuild_sqlite_settings(db, inspector):
    logger.info("Rebuilding SQLite settings table for per-user ownership")
    columns = _column_names(inspector, "settings")
    user_id_expr = "user_id" if "user_id" in columns else "NULL"

    db.execute(text("""
        CREATE TABLE settings_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            key VARCHAR(255) NOT NULL,
            value TEXT,
            CONSTRAINT uq_settings_user_key UNIQUE (user_id, key),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """))
    db.execute(text(f"""
        INSERT INTO settings_new (id, user_id, key, value)
        SELECT id, {user_id_expr}, key, value
        FROM settings
    """))
    db.execute(text("DROP TABLE settings"))
    db.execute(text("ALTER TABLE settings_new RENAME TO settings"))
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_settings_user_id ON settings (user_id)"))
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_settings_key ON settings (key)"))


def _ensure_mysql_projects_ownership(db, inspector):
    columns = _column_names(inspector, "projects")
    if not columns:
        return

    if "user_id" not in columns:
        logger.info("Adding user_id column to MySQL projects table")
        db.execute(text("ALTER TABLE projects ADD COLUMN user_id INT NULL"))
        owner_id = _single_user_id(db)
        if owner_id is not None:
            db.execute(text("UPDATE projects SET user_id = :owner_id WHERE user_id IS NULL"), {"owner_id": owner_id})

    inspector = _get_inspector()
    for constraint in _unique_constraints(inspector, "projects"):
        if constraint.get("column_names") == ["name"] and constraint.get("name"):
            logger.info("Dropping legacy unique constraint on projects.name")
            db.execute(text(f"ALTER TABLE projects DROP INDEX {constraint['name']}"))

    indexes = _index_names(_get_inspector(), "projects")
    if "ix_projects_user_id" not in indexes:
        db.execute(text("CREATE INDEX ix_projects_user_id ON projects (user_id)"))

    foreign_keys = _foreign_key_names(_get_inspector(), "projects")
    if "fk_projects_user_id" not in foreign_keys:
        db.execute(text("""
            ALTER TABLE projects
            ADD CONSTRAINT fk_projects_user_id FOREIGN KEY (user_id) REFERENCES users(id)
        """))

    uniques = _unique_constraints(_get_inspector(), "projects")
    if not any(constraint.get("name") == "uq_projects_user_name" for constraint in uniques):
        db.execute(text("""
            ALTER TABLE projects
            ADD CONSTRAINT uq_projects_user_name UNIQUE (user_id, name)
        """))


def _ensure_mysql_settings_ownership(db, inspector):
    columns = _column_names(inspector, "settings")
    if not columns:
        return

    if "user_id" not in columns:
        logger.info("Adding user_id column to MySQL settings table")
        db.execute(text("ALTER TABLE settings ADD COLUMN user_id INT NULL"))

    inspector = _get_inspector()
    for constraint in _unique_constraints(inspector, "settings"):
        if constraint.get("column_names") == ["key"] and constraint.get("name"):
            logger.info("Dropping legacy unique constraint on settings.key")
            db.execute(text(f"ALTER TABLE settings DROP INDEX {constraint['name']}"))

    indexes = _index_names(_get_inspector(), "settings")
    if "ix_settings_user_id" not in indexes:
        db.execute(text("CREATE INDEX ix_settings_user_id ON settings (user_id)"))

    foreign_keys = _foreign_key_names(_get_inspector(), "settings")
    if "fk_settings_user_id" not in foreign_keys:
        db.execute(text("""
            ALTER TABLE settings
            ADD CONSTRAINT fk_settings_user_id FOREIGN KEY (user_id) REFERENCES users(id)
        """))

    uniques = _unique_constraints(_get_inspector(), "settings")
    if not any(constraint.get("name") == "uq_settings_user_key" for constraint in uniques):
        db.execute(text("""
            ALTER TABLE settings
            ADD CONSTRAINT uq_settings_user_key UNIQUE (user_id, `key`)
        """))


def migrate_schema():
    """Handle additive schema updates for existing databases."""
    with session_lock:
        db = SessionLocal()
        try:
            dialect = engine.dialect.name
            inspector = _get_inspector()

            _ensure_prompts_table(db, dialect, inspector)
            db.commit()

            inspector = _get_inspector()
            _ensure_recordings_prompt_id(db, dialect, inspector)
            _ensure_projects_is_rtl(db, dialect, inspector)
            db.commit()

            inspector = _get_inspector()
            if dialect == "sqlite":
                if _sqlite_projects_need_rebuild(inspector):
                    _rebuild_sqlite_projects(db, inspector)
                    db.commit()
                    inspector = _get_inspector()

                if _sqlite_settings_need_rebuild(inspector):
                    _rebuild_sqlite_settings(db, inspector)
                    db.commit()
            else:
                _ensure_mysql_projects_ownership(db, inspector)
                db.commit()
                inspector = _get_inspector()
                _ensure_mysql_settings_ownership(db, inspector)
                db.commit()

            logger.info("Schema migration completed")
        except Exception as exc:
            db.rollback()
            logger.exception("Schema migration failed: %s", exc)
        finally:
            db.close()
