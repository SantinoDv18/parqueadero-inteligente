
import cv2
import argparse
_ap = argparse.ArgumentParser()
_ap.add_argument("--imagen", default="zona_parqueadero.jpg")
_ap.add_argument("--plazas", default="plazas.json")
_args = _ap.parse_args()
import json
import numpy as np

# Cargar imagen
imagen = cv2.imread(_args.imagen)

if imagen is None:
    print("No se pudo cargar la imagen.")
    exit()

alto, ancho = imagen.shape[:2]

print(f"Resolucion de la imagen: {ancho} x {alto}")

# Cargar plazas
with open(_args.plazas, "r", encoding="utf-8") as archivo:
    plazas = json.load(archivo)

print(f"Plazas encontradas: {len(plazas)}")

resultado = imagen.copy()

for plaza in plazas:

    nombre = plaza["nombre"]
    puntos = plaza["puntos"]

    # Convertir coordenadas a NumPy
    puntos_np = np.array(
        puntos,
        dtype=np.int32
    )

    # Comprobar coordenadas
    fuera_imagen = any(
        x < 0 or x >= ancho or y < 0 or y >= alto
        for x, y in puntos
    )

    if fuera_imagen:
        print(f"ADVERTENCIA: {nombre} tiene puntos fuera de la imagen.")

    # Dibujar poligono
    cv2.polylines(
        resultado,
        [puntos_np.reshape((-1, 1, 2))],
        True,
        (0, 255, 0),
        1
    )

    # Calcular centro
    centro_x = int(np.mean(puntos_np[:, 0]))
    centro_y = int(np.mean(puntos_np[:, 1]))

    cv2.putText(
        resultado,
        nombre,
        (centro_x, centro_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.35,
        (0, 255, 255),
        1
    )

# Mostrar resultado
cv2.imshow("Validacion de plazas", resultado)

cv2.waitKey(0)
cv2.destroyAllWindows()
