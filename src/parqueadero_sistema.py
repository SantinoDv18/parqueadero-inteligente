"""
Parqueadero inteligente - sistema de punta a punta (Avance 2)

Flujo: video/camara -> YOLO -> cobertura carro/cupo -> suavizado -> SQLite -> video anotado

Uso rapido (desde la raiz del repositorio, ver README.md):
  python src/parqueadero_sistema.py --fuente video.mp4 --ref-frame 100
  python src/parqueadero_sistema.py --fuente video.mp4 --exportar 12
  python src/parqueadero_sistema.py --fuente video.mp4 --gt data/talatshii/gt.json
  python src/parqueadero_sistema.py --fuente https://youtu.be/gQUoJ6inXK4 --roi 305,85,570,235 --plazas data/camara_publica/plazas.json
"""
import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta

import cv2
import numpy as np

CLASES_VEHICULO = [2, 3, 5, 7]  # carro, moto, bus, camion (COCO)

SCHEMA = """
CREATE TABLE IF NOT EXISTS cupos (
    id INTEGER PRIMARY KEY,
    zona TEXT,
    poligono_json TEXT
);
CREATE TABLE IF NOT EXISTS estados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cupo_id INTEGER REFERENCES cupos(id),
    momento TIMESTAMP,
    ocupado BOOLEAN
);
CREATE TABLE IF NOT EXISTS resumen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    momento TIMESTAMP,
    libres INTEGER,
    ocupados INTEGER
);
"""


# ---------------------------------------------------------------- utilidades
def abrir_fuente(fuente):
    """Archivo local o enlace de YouTube (usa yt_dlp como en test_camera.py)."""
    if fuente.startswith("http"):
        r = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "-f", "230", "-g",
             "--no-warnings", "--no-playlist", fuente],
            capture_output=True, text=True)
        if r.returncode != 0 or not r.stdout.strip():
            sys.exit("No se pudo obtener la transmision:\n" + r.stderr)
        return cv2.VideoCapture(r.stdout.strip().splitlines()[0], cv2.CAP_FFMPEG), True
    return cv2.VideoCapture(fuente), False


def parse_roi(texto):
    if not texto:
        return None
    x1, y1, x2, y2 = [int(v) for v in texto.split(",")]
    return x1, y1, x2, y2


def recortar(frame, roi):
    if roi is None:
        return frame
    x1, y1, x2, y2 = roi
    return frame[y1:y2, x1:x2]


def iniciar_db(ruta, plazas):
    con = sqlite3.connect(ruta)
    con.executescript(SCHEMA)
    for i, p in enumerate(plazas, start=1):
        con.execute(
            "INSERT OR REPLACE INTO cupos (id, zona, poligono_json) VALUES (?,?,?)",
            (i, p["nombre"], json.dumps(p["puntos"])))
    con.commit()
    return con


# ---------------------------------------------------------------- logica
def cobertura_por_plaza(cajas, mascaras, areas):
    """Fraccion del area del cupo cubierta por el carro que mas lo cubre."""
    resultado = []
    for mask, area in zip(mascaras, areas):
        mejor = 0.0
        for (x1, y1, x2, y2) in cajas:
            inter = np.count_nonzero(mask[max(y1, 0):y2, max(x1, 0):x2])
            mejor = max(mejor, inter / area)
        resultado.append(mejor)
    return resultado


def metricas(gt, registros, nombres):
    """registros: {frame: {'crudo': [0/1..], 'suave': [0/1..]}}"""
    for clave in ("crudo", "suave"):
        tp = fp = fn = tn = 0
        for frame, real in gt.items():
            if int(frame) not in registros:
                continue
            pred = registros[int(frame)][clave]
            for i, nombre in enumerate(nombres):
                if nombre not in real:
                    continue
                r, p = int(real[nombre]), int(pred[i])
                tp += r and p
                tn += (not r) and (not p)
                fp += (not r) and p
                fn += r and (not p)
        total = tp + tn + fp + fn
        if total == 0:
            print("Sin fotogramas de prueba evaluables.")
            return
        prec = tp / (tp + fp) if tp + fp else 0
        rec = tp / (tp + fn) if tp + fn else 0
        print(f"\nMETRICAS ({clave}) sobre {total} decisiones de cupo")
        print(f"  Exactitud: {(tp + tn) / total:.3f} | Precision: {prec:.3f} | Recall: {rec:.3f}")
        print(f"  TP={tp} TN={tn} FP={fp} FN={fn}")


# ---------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fuente", required=True, help="video.mp4 o enlace de YouTube")
    ap.add_argument("--plazas", default="data/talatshii/plazas.json")
    ap.add_argument("--modelo", default="yolo11n.pt")
    ap.add_argument("--db", default="db/parqueadero.db")
    ap.add_argument("--salida", default="results/resultado.mp4")
    ap.add_argument("--roi", default=None, help="x1,y1,x2,y2 (solo si dibujaste cupos sobre un recorte)")
    ap.add_argument("--conf", type=float, default=0.35)
    ap.add_argument("--imgsz", type=int, default=960)
    ap.add_argument("--umbral", type=float, default=0.30, help="cobertura minima carro/cupo")
    ap.add_argument("--estable", type=int, default=5, help="decisiones seguidas para cambiar estado")
    ap.add_argument("--salto", type=int, default=3, help="procesar 1 de cada N fotogramas")
    ap.add_argument("--max-seg", type=float, default=0, help="limitar duracion (0 = todo)")
    ap.add_argument("--gt", default=None, help="json con etiquetas reales para metricas")
    ap.add_argument("--ref-salida", default="data/talatshii/zona_parqueadero.jpg", help="donde guardar el fotograma de referencia")
    ap.add_argument("--pruebas", default="data/talatshii/pruebas", help="carpeta de fotogramas de prueba")
    ap.add_argument("--ref-frame", type=int, default=None, help="guardar fotograma N como zona_parqueadero.jpg y salir")
    ap.add_argument("--exportar", type=int, default=0, help="guardar N fotogramas de prueba en pruebas/ y salir")
    args = ap.parse_args()

    roi = parse_roi(args.roi)
    cap, es_vivo = abrir_fuente(args.fuente)
    if not cap.isOpened():
        sys.exit("No se pudo abrir la fuente.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # --- modos auxiliares
    if args.ref_frame is not None:
        cap.set(cv2.CAP_PROP_POS_FRAMES, args.ref_frame)
        ok, fr = cap.read()
        os.makedirs(os.path.dirname(args.ref_salida) or ".", exist_ok=True)
        cv2.imwrite(args.ref_salida, recortar(fr, roi))
        print(f"Guardado {args.ref_salida}. Ahora corre src/herramientas/definir_plazas.py")
        return
    if args.exportar:
        os.makedirs(args.pruebas, exist_ok=True)
        for idx in np.linspace(0, total_frames - 2, args.exportar).astype(int):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ok, fr = cap.read()
            if ok:
                cv2.imwrite(f"{args.pruebas}/frame_{idx:05d}.jpg", recortar(fr, roi))
        print(f"Fotogramas en {args.pruebas}/. Etiquetalos con src/etiquetar_gt.py")
        return

    # --- carga
    from ultralytics import YOLO
    model = YOLO(args.modelo)
    with open(args.plazas, "r", encoding="utf-8") as f:
        plazas = json.load(f)
    nombres = [p["nombre"] for p in plazas]
    gt = json.load(open(args.gt)) if args.gt else {}
    gt_frames = {int(k) for k in gt}

    os.makedirs(os.path.dirname(args.db) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(args.salida) or ".", exist_ok=True)
    con = iniciar_db(args.db, plazas)
    n = len(plazas)

    ok, frame = cap.read()
    if not ok:
        sys.exit("No se pudo leer el primer fotograma.")
    zona = recortar(frame, roi)
    alto, ancho = zona.shape[:2]

    mascaras, areas = [], []
    for p in plazas:
        m = np.zeros((alto, ancho), np.uint8)
        cv2.fillPoly(m, [np.array(p["puntos"], np.int32)], 1)
        mascaras.append(m)
        areas.append(max(int(m.sum()), 1))

    writer = cv2.VideoWriter(args.salida, cv2.VideoWriter_fourcc(*"mp4v"), fps, (ancho, alto))

    inicio = datetime.now()
    estado = [None] * n          # estado confirmado (suavizado)
    contador = [0] * n           # decisiones seguidas que contradicen el estado
    cajas = []
    registros = {}
    cambios = 0
    idx = 0
    t0 = time.time()
    procesados = 0

    while ok:
        zona = recortar(frame, roi)
        if idx % args.salto == 0 or idx in gt_frames:
            res = model.predict(zona, conf=args.conf, imgsz=args.imgsz,
                                classes=CLASES_VEHICULO, iou=0.45, verbose=False)[0]
            cajas = [tuple(map(int, b.xyxy[0].tolist())) for b in res.boxes]
            cob = cobertura_por_plaza(cajas, mascaras, areas)
            crudo = [int(c >= args.umbral) for c in cob]
            momento = (inicio + timedelta(seconds=idx / fps)).isoformat(timespec="seconds")

            # suavizado: cambia solo si la nueva lectura se mantiene
            for i in range(n):
                if estado[i] is None:
                    estado[i] = crudo[i]
                    con.execute("INSERT INTO estados (cupo_id, momento, ocupado) VALUES (?,?,?)",
                                (i + 1, momento, estado[i]))
                elif crudo[i] != estado[i]:
                    contador[i] += 1
                    if contador[i] >= args.estable:
                        estado[i] = crudo[i]
                        contador[i] = 0
                        cambios += 1
                        con.execute("INSERT INTO estados (cupo_id, momento, ocupado) VALUES (?,?,?)",
                                    (i + 1, momento, estado[i]))
                else:
                    contador[i] = 0

            ocupados = sum(estado)
            if procesados % 10 == 0:
                con.execute("INSERT INTO resumen (momento, libres, ocupados) VALUES (?,?,?)",
                            (momento, n - ocupados, ocupados))
            con.commit()
            registros[idx] = {"crudo": crudo, "suave": list(estado)}
            procesados += 1

        # --- dibujo
        vis = zona.copy()
        for (x1, y1, x2, y2) in cajas:
            cv2.rectangle(vis, (x1, y1), (x2, y2), (255, 120, 0), 1)
        for p, e in zip(plazas, estado):
            color = (0, 0, 255) if e else (0, 200, 0)
            cv2.polylines(vis, [np.array(p["puntos"], np.int32).reshape(-1, 1, 2)], True, color, 2)
        ocupados = sum(e or 0 for e in estado)
        cv2.rectangle(vis, (0, 0), (ancho, 28), (0, 0, 0), -1)
        cv2.putText(vis, f"Libres: {n - ocupados}  Ocupados: {ocupados}  Total: {n}",
                    (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        writer.write(vis)

        idx += 1
        if args.max_seg and idx / fps >= args.max_seg:
            break
        if es_vivo:
            cv2.imshow("Parqueadero", vis)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        ok, frame = cap.read()

    cap.release()
    writer.release()
    cv2.destroyAllWindows()
    cv2.imwrite(os.path.splitext(args.salida)[0] + "_final.jpg", vis)

    seg = time.time() - t0
    print("\nESTADO FINAL DEL PARQUEADERO")
    print(f"Total: {n} | Ocupados: {sum(estado)} | Libres: {n - sum(estado)}")
    print(f"Cambios de estado confirmados: {cambios}")
    print(f"Fotogramas leidos: {idx} | analizados con YOLO: {procesados} | {procesados / seg:.1f} FPS de analisis")
    print(f"Base de datos: {args.db} | Video: {args.salida}")

    if gt:
        metricas(gt, registros, nombres)
    con.close()


if __name__ == "__main__":
    main()
