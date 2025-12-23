-- Таблица источников
CREATE TABLE IF NOT EXISTS source (
    id SERIAL PRIMARY KEY,
    url VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица логов
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    source_id INT NOT NULL,
    celery_task_id VARCHAR(255),
    status VARCHAR(20),
    error_code VARCHAR(50),
    error_message TEXT,
    items_parsed INT DEFAULT 0,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    duration_seconds INT,
    FOREIGN KEY (source_id) REFERENCES source(id)
);

-- Таблица для Dohod
CREATE TABLE IF NOT EXISTS dohod_divs (
    id SERIAL PRIMARY KEY,
    source_id INT NOT NULL,
    ticker VARCHAR(20),
    company_name VARCHAR(255),
    sector VARCHAR(100),
    period VARCHAR(100),
    payment_per_share DECIMAL(10, 4),
    currency VARCHAR(10),
    yield_percent DECIMAL(10, 2),
    record_date_estimate DATE,
    capitalization_mln_rub DECIMAL(20, 2),
    dsi DECIMAL(10, 2),
    parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES source(id)
);

-- Таблица для RBC
CREATE TABLE IF NOT EXISTS rbc_news (
    id SERIAL PRIMARY KEY,
    source_id INT NOT NULL,
    title TEXT,
    url TEXT UNIQUE,
    text TEXT,
    parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES source(id)
);

-- Таблица для SmartLab
CREATE TABLE IF NOT EXISTS smartlab_stocks (
    id SERIAL PRIMARY KEY,
    source_id INT NOT NULL,
    name VARCHAR(255),
    ticker VARCHAR(20),
    last_price_rub DECIMAL(10, 2),
    price_change_percent DECIMAL(10, 2),
    volume_mln_rub DECIMAL(20, 2),
    change_week_percent DECIMAL(10, 2),
    change_month_percent DECIMAL(10, 2),
    change_ytd_percent DECIMAL(10, 2),
    change_year_percent DECIMAL(10, 2),
    capitalization_bln_rub DECIMAL(20, 2),
    capitalization_bln_usd DECIMAL(20, 2),
    parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES source(id)
);

-- Индексы для быстрого поиска
CREATE INDEX idx_logs_source_id ON logs(source_id);
CREATE INDEX idx_dohod_ticker ON dohod_divs(ticker);
CREATE INDEX idx_rbc_url ON rbc_news(url);
CREATE INDEX idx_smartlab_ticker ON smartlab_stocks(ticker);

-- Начальные данные
INSERT INTO source (url, name) VALUES
    ('https://www.rbc.ru/quote', 'RBC'),
    ('https://smart-lab.ru/q/shares/', 'SmartLab'),
    ('https://www.dohod.ru/ik/analytics/share', 'Dohod')
ON CONFLICT (url) DO NOTHING;

