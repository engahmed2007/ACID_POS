-- ==========================================================
-- مخطط قاعدة البيانات - برنامج بيع وإدارة مخزون ماء النار
-- ==========================================================

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS employees (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    password_salt   TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('manager', 'employee')),
    permissions     TEXT NOT NULL DEFAULT '',   -- صلاحيات مفصّلة (مفصولة بفاصلة) يتحكم فيها المدير
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS products (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL UNIQUE,
    current_quantity_kg REAL NOT NULL DEFAULT 0,
    alert_threshold_kg  REAL NOT NULL DEFAULT 0,
    is_active           INTEGER NOT NULL DEFAULT 1,
    created_at          TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS daily_prices (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id    INTEGER NOT NULL REFERENCES products(id),
    price_per_kg  REAL NOT NULL,
    date          TEXT NOT NULL DEFAULT (date('now', 'localtime')),
    set_by        INTEGER REFERENCES employees(id),
    created_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS customers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT UNIQUE,               -- كود مختصر مميز لكل عميل (مثال: C0001)
    name        TEXT NOT NULL,
    phone       TEXT,
    total_debt  REAL NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS invoices (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    date_time     TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    customer_id   INTEGER REFERENCES customers(id),
    employee_id   INTEGER NOT NULL REFERENCES employees(id),
    is_printed    INTEGER NOT NULL DEFAULT 0,
    is_credit     INTEGER NOT NULL DEFAULT 0,
    subtotal_amount REAL NOT NULL DEFAULT 0,
    discount_amount REAL NOT NULL DEFAULT 0,
    total_amount  REAL NOT NULL DEFAULT 0,
    is_deleted    INTEGER NOT NULL DEFAULT 0,
    notes         TEXT
);

CREATE TABLE IF NOT EXISTS invoice_items (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id            INTEGER NOT NULL REFERENCES invoices(id),
    product_id            INTEGER NOT NULL REFERENCES products(id),
    quantity_kg           REAL NOT NULL,
    price_per_kg_at_sale  REAL NOT NULL,
    purchase_price_per_kg REAL,
    line_total            REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id   INTEGER NOT NULL REFERENCES customers(id),
    amount        REAL NOT NULL,
    date          TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    received_by   INTEGER REFERENCES employees(id),
    notes         TEXT
);

CREATE TABLE IF NOT EXISTS stock_movements (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id          INTEGER NOT NULL REFERENCES products(id),
    movement_type       TEXT NOT NULL CHECK (movement_type IN ('in', 'out')),
    quantity_kg         REAL NOT NULL,
    balance_after_kg    REAL NOT NULL,
    date                TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    related_invoice_id  INTEGER REFERENCES invoices(id),
    purchase_price_per_kg REAL,
    notes               TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id   INTEGER REFERENCES employees(id),
    action        TEXT NOT NULL,
    entity_type   TEXT NOT NULL,
    entity_id     INTEGER,
    details       TEXT,
    date_time     TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(date_time);
CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements(product_id);
CREATE INDEX IF NOT EXISTS idx_daily_prices_product_date ON daily_prices(product_id, date);
