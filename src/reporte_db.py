"""Consultas de ejemplo sobre la base de datos (sirve como evidencia y como base del tablero).

Uso: python src/reporte_db.py [--db db/parqueadero.db]
"""
import argparse
import sqlite3

ap = argparse.ArgumentParser()
ap.add_argument("--db", default="db/parqueadero.db")
args = ap.parse_args()

con = sqlite3.connect(args.db)


def mostrar(titulo, sql):
    print(f"\n== {titulo} ==")
    filas = con.execute(sql).fetchall()
    if not filas:
        print("(sin datos)")
    for f in filas:
        print(" | ".join(str(c) for c in f))


ULTIMO = "SELECT MAX(id) FROM estados GROUP BY cupo_id"

mostrar("Estado actual de cada cupo (1 = ocupado)",
        f"""SELECT c.zona, e.ocupado, e.momento
            FROM estados e JOIN cupos c ON c.id = e.cupo_id
            WHERE e.id IN ({ULTIMO}) ORDER BY c.id""")

mostrar("Cupos libres ahora",
        f"SELECT COUNT(*) FROM estados WHERE id IN ({ULTIMO}) AND ocupado = 0")

mostrar("Cambios de estado por cupo",
        """SELECT c.zona, COUNT(*) AS registros
           FROM estados e JOIN cupos c ON c.id = e.cupo_id
           GROUP BY c.id ORDER BY registros DESC""")

mostrar("Ocupacion promedio por hora",
        """SELECT strftime('%H', momento) AS hora,
                  ROUND(AVG(ocupados * 1.0 / (libres + ocupados)), 2) AS ocupacion
           FROM resumen GROUP BY hora ORDER BY hora""")

mostrar("Ultimos 10 registros del resumen",
        "SELECT momento, libres, ocupados FROM resumen ORDER BY id DESC LIMIT 10")
con.close()
