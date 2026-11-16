
import cv2
import argparse
_ap = argparse.ArgumentParser()
_ap.add_argument("--imagen", default="zona_parqueadero.jpg")
_ap.add_argument("--plazas", default="plazas.json")
_args = _ap.parse_args()
import json
import os
import numpy as np
# 1. Cargar imagen de nuestra zona
imagen = cv2.imread(_args.imagen)

if imagen is None:
    print("No se pudo cargar la imagen.")
    exit()

# Copia para dibujar
imagen_base = imagen.copy()

# Lista de plazas terminadas
plazas = []

# Puntos de la plaza actual
puntos_actuales = []


# 2. Funcion para dibujar los poligonos

def dibujar():

    resultado = imagen_base.copy()

    # Dibujar plazas terminadas
    for i, plaza in enumerate(plazas):

        # Convertir puntos al formato requerido por OpenCV
        puntos_lista = plaza["puntos"]

        puntos_cv = np.array(
            puntos_lista,
            dtype=np.int32
        ).reshape((-1, 1, 2))

        cv2.polylines(
            resultado,
            [puntos_cv],
            True,
            (0, 255, 0),
            2
        )

        # Calcular centro del poligono
        centro_x = int(
            sum(p[0] for p in puntos_lista) / len(puntos_lista)
        )

        centro_y = int(
            sum(p[1] for p in puntos_lista) / len(puntos_lista)
        )

        cv2.putText(
            resultado,
            plaza["nombre"],
            (centro_x, centro_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1
        )

    # Dibujar puntos de la plaza actual
    for punto in puntos_actuales:

        cv2.circle(
            resultado,
            punto,
            4,
            (0, 0, 255),
            -1
        )

    # Dibujar lineas entre puntos actuales
    if len(puntos_actuales) > 1:

        for i in range(len(puntos_actuales) - 1):

            cv2.line(
                resultado,
                puntos_actuales[i],
                puntos_actuales[i + 1],
                (0, 0, 255),
                2
            )

    # Instrucciones
    cv2.putText(
        resultado,
        "Click: puntos | C: cerrar plaza | U: deshacer",
        (5, 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.35,
        (255, 255, 255),
        1
    )

    cv2.putText(
        resultado,
        "S: guardar | R: reiniciar actual | Q: salir",
        (5, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.35,
        (255, 255, 255),
        1
    )

    return resultado



# 3. Detectar clics del raton
def seleccionar_punto(event, x, y, flags, param):

    if event == cv2.EVENT_LBUTTONDOWN:

        puntos_actuales.append((x, y))


# 4. Crear ventana
cv2.namedWindow("Delimitar plazas")

cv2.setMouseCallback(
    "Delimitar plazas",
    seleccionar_punto
)

print("Herramienta de delimitacion iniciada.")

print("Haz clic en las esquinas de cada plaza.")
print("Presiona C para cerrar cada poligono.")
print("Presiona S para guardar las plazas.")

# 5. Bucle principal
while True:

    cv2.imshow(
        "Delimitar plazas",
        dibujar()
    )

    tecla = cv2.waitKey(20) & 0xFF

    # Cerrar poligono
    if tecla == ord("c"):

        if len(puntos_actuales) >= 3:

            nombre = f"plaza_{len(plazas) + 1}"

            plazas.append({
                "nombre": nombre,
                "puntos": puntos_actuales.copy()
            })

            print(f"{nombre} delimitada.")

            puntos_actuales.clear()

        else:

            print("Necesitas al menos 3 puntos.")

    # Deshacer ultimo punto
    elif tecla == ord("u"):

        if puntos_actuales:

            puntos_actuales.pop()

    # Reiniciar plaza actual
    elif tecla == ord("r"):

        puntos_actuales.clear()

        print("Poligono actual reiniciado.")

    # Guardar plazas
    elif tecla == ord("s"):

        if puntos_actuales:
            print("Cierra el poligono actual antes de guardar.")
            continue

        with open(_args.plazas, "w", encoding="utf-8") as archivo:

            json.dump(
                plazas,
                archivo,
                indent=4
            )

        print(f"Se guardaron {len(plazas)} plazas.")

    # Salir
    elif tecla == ord("q"):

        break


cv2.destroyAllWindows()
