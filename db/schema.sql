-- Modelo de base de datos del parqueadero inteligente (SQLite)
-- El script src/parqueadero_sistema.py crea estas mismas tablas automaticamente.

-- Un cupo se define una sola vez como poligono (lista de puntos x, y en pixeles).
CREATE TABLE IF NOT EXISTS cupos (
    id INTEGER PRIMARY KEY,
    zona TEXT,
    poligono_json TEXT
);

-- Solo se guarda un registro cuando el estado de un cupo CAMBIA (ya suavizado).
CREATE TABLE IF NOT EXISTS estados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cupo_id INTEGER REFERENCES cupos(id),
    momento TIMESTAMP,
    ocupado BOOLEAN
);

-- Serie de tiempo del total de cupos libres y ocupados (base del tablero).
CREATE TABLE IF NOT EXISTS resumen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    momento TIMESTAMP,
    libres INTEGER,
    ocupados INTEGER
);
