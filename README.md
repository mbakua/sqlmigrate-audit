# sqlmigrate-audit

> Lightweight library to track and annotate SQL migration history with rollback metadata

---

## Installation

```bash
pip install sqlmigrate-audit
```

Or with optional database extras:

```bash
pip install sqlmigrate-audit[postgres]
```

---

## Usage

```python
from sqlmigrate_audit import MigrationAuditor

auditor = MigrationAuditor(db_url="postgresql://user:pass@localhost/mydb")

# Record a migration with rollback metadata
auditor.record(
    migration_id="0042_add_users_table",
    sql_up="CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT);",
    sql_down="DROP TABLE users;",
    author="alice",
    tags=["schema", "users"],
)

# List migration history
for entry in auditor.history():
    print(f"[{entry.applied_at}] {entry.migration_id} — {entry.author}")

# Roll back the last migration
auditor.rollback(migration_id="0042_add_users_table")
```

Migration records are stored in a dedicated audit table (`_sqlmigrate_audit`) within your database, keeping your history portable and queryable.

---

## Features

- 📋 Tracks applied migrations with timestamps and author metadata
- ↩️ Stores rollback SQL alongside each migration for safe reversions
- 🏷️ Supports tagging and annotation for easy filtering
- 🔌 Works with PostgreSQL, MySQL, and SQLite

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss any major changes.

---

## License

[MIT](LICENSE)