"""
Etiquetar la ocupacion REAL de cada cupo en los fotogramas de prueba (pruebas/frame_XXXXX.jpg).

Antes:  python src/parqueadero_sistema.py --fuente video.mp4 --exportar 12
Uso:    python src/etiquetar_gt.py
  - Clic dentro de un cupo: alterna libre (verde) / ocupado (rojo).
  - N = guardar y pasar al siguiente | B = anterior | Q = guardar y salir.
Regla: etiqueta segun el cupo FISICO al que corresponde cada poligono, aunque el
poligono quede desfasado por el movimiento de la camara. Asi el desfase cuenta como error.
"""
import argparse
import glob
import json
import os
import re

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--plazas", default="data/talatshii/plazas.json")
ap.add_argument("--pruebas", default="data/talatshii/pruebas")
ap.add_argument("--gt", default="data/talatshii/gt.json")
args = ap.parse_args()

with open(args.plazas, "r", encoding="utf-8") as f:
    plazas = json.load(f)
polys = [np.array(p["puntos"], np.int32) for p in plazas]

archivos = sorted(glob.glob(f"{args.pruebas}/frame_*.jpg"))
if not archivos:
    raise SystemExit("No hay fotogramas en pruebas/. Usa --exportar primero.")

gt = json.load(open(args.gt)) if os.path.exists(args.gt) else {}
i = 0
estado = []


def clave(ruta):
    return str(int(re.search(r"frame_(\d+)", ruta).group(1)))


def cargar(idx):
    k = clave(archivos[idx])
    return [int(gt.get(k, {}).get(p["nombre"], 0)) for p in plazas]


def guardar(idx):
    gt[clave(archivos[idx])] = {p["nombre"]: int(e) for p, e in zip(plazas, estado)}
    with open(args.gt, "w", encoding="utf-8") as f:
        json.dump(gt, f, indent=2)


def clic(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        for j, poly in enumerate(polys):
            if cv2.pointPolygonTest(poly.reshape(-1, 1, 2), (float(x), float(y)), False) >= 0:
                estado[j] = 1 - estado[j]
                break


cv2.namedWindow("Etiquetar")
cv2.setMouseCallback("Etiquetar", clic)
estado = cargar(i)

while True:
    img = cv2.imread(archivos[i])
    for j, (poly, e) in enumerate(zip(polys, estado)):
        color = (0, 0, 255) if e else (0, 200, 0)
        cv2.polylines(img, [poly.reshape(-1, 1, 2)], True, color, 2)
        cx, cy = poly.mean(axis=0).astype(int)
        cv2.putText(img, str(j + 1), (cx - 6, cy + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.putText(img, f"{i + 1}/{len(archivos)}  N=sig  B=ant  Q=salir",
                (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.imshow("Etiquetar", img)
    t = cv2.waitKey(30) & 0xFF
    if t == ord("n"):
        guardar(i)
        if i < len(archivos) - 1:
            i += 1
            estado = cargar(i)
    elif t == ord("b") and i > 0:
        guardar(i)
        i -= 1
        estado = cargar(i)
    elif t == ord("q"):
        guardar(i)
        break

cv2.destroyAllWindows()
print(f"Guardado {args.gt} con {len(gt)} fotogramas etiquetados.")
