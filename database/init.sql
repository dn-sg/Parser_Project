CREATE TABLE IF NOT EXISTS source (
    id SERIAL PRIMARY KEY,
    url VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS parsed_data (
    id SERIAL PRIMARY KEY,
    source_id INT NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    price DECIMAL(10, 2),
    change DECIMAL(5, 2),
    volume BIGINT,
    raw_data JSONB,
    parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES source(id)
);


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


CREATE INDEX idx_parsed_data_source_id ON parsed_data(source_id);
CREATE INDEX idx_parsed_data_ticker ON parsed_data(ticker);
CREATE INDEX idx_logs_source_id ON logs(source_id);
CREATE INDEX idx_logs_celery_task_id ON logs(celery_task_id);
CREATE INDEX idx_logs_status ON logs(status);


INSERT INTO source (url, name) VALUES
    ('https://www.rbc.ru/quote', 'RBC'),
    ('https://smart-lab.ru/q/shares/', 'SmartLab'),
    ('https://www.dohod.ru/ik/analytics/share', 'Dohod')
ON CONFLICT (url) DO NOTHING;