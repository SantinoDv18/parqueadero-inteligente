
import cv2
import json
import numpy as np
from ultralytics import YOLO

# 1. Cargar modelo
model = YOLO("yolo11n.pt")

# 2. Cargar imagen de la zona
imagen = cv2.imread("zona_parqueadero.jpg")

if imagen is None:
    print("No se pudo cargar la imagen.")
    exit()

# 3. Cargar poligonos
with open("plazas.json", "r", encoding="utf-8") as archivo:
    plazas = json.load(archivo)

# 4. Ejecutar YOLO
result = model.predict(
    source=imagen,
    conf=0.50,
    imgsz=640,
    classes=[2, 3, 5, 7],
    verbose=False
)[0]

for indice, box in enumerate(result.boxes):

    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

    centro_x = (x1 + x2) // 2
    centro_y = (y1 + y2) // 2
    
    
    cv2.rectangle(
        imagen,
        (x1, y1),
        (x2, y2),
        (255, 0, 0),
        1
    )

    cv2.putText(
        imagen,
        str(indice + 1),
        (centro_x, centro_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.4,
        (255, 0, 0),
        1
    )
    
    

# 5. Crear conjunto de plazas ocupadas
plazas_ocupadas = set()

for indice, box in enumerate(result.boxes):

    x1, y1, x2, y2 = box.xyxy[0].tolist()

    punto_x = int((x1 + x2) / 2)
    punto_y = int(y2)
    
    cv2.circle(
        imagen,
        (punto_x, punto_y),
        3,
        (255, 0, 0),
        -1
        )
    
    cv2.putText(
        imagen,
        str(indice + 1),
        (punto_x + 3, punto_y - 3),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.35,
        (255, 0, 0),
        1
    )

    plazas_detectadas = []

    for plaza in plazas:

        puntos = np.array(
            plaza["puntos"],
            dtype=np.int32
        ).reshape((-1, 1, 2))

        resultado = cv2.pointPolygonTest(
            puntos,
            (float(punto_x), float(punto_y)),
            False
        )

        if resultado >= 0:
            plazas_detectadas.append(plaza["nombre"])

    if plazas_detectadas:
        print(
            f"Vehiculo {indice + 1}: "
            f"{plazas_detectadas}"
        )

        for nombre in plazas_detectadas:
            plazas_ocupadas.add(nombre)

# 6. Recorrer vehiculos detectados
for box in result.boxes:

    # Obtener coordenadas del vehiculo
    x1, y1, x2, y2 = box.xyxy[0].tolist()

    # Calcular punto inferior central
    punto_x = int((x1 + x2) / 2)
    punto_y = int(y2)

    # Comprobar si el punto esta dentro de alguna plaza
    for plaza in plazas:

        puntos = np.array(
            plaza["puntos"],
            dtype=np.int32
        )

        resultado = cv2.pointPolygonTest(
            puntos,
            (float(punto_x), float(punto_y)),
            False
        )

        if resultado >= 0:
            plazas_ocupadas.add(plaza["nombre"])

# 7. Dibujar estado de las plazas
imagen_resultado = imagen.copy()

for plaza in plazas:

    puntos = np.array(
        plaza["puntos"],
        dtype=np.int32
    ).reshape((-1, 1, 2))

    nombre = plaza["nombre"]

    ocupada = nombre in plazas_ocupadas

    if ocupada:
        color = (0, 0, 255)
    else:
        color = (0, 255, 0)

    # Dibujar poligono
    cv2.polylines(
        imagen_resultado,
        [puntos],
        True,
        color,
        2
    )

    # Calcular centro
    centro_x = int(np.mean(puntos[:, 0, 0]))
    centro_y = int(np.mean(puntos[:, 0, 1]))

    # Dibujar nombre
    cv2.putText(
        imagen_resultado,
        nombre,
        (centro_x, centro_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.30,
        color,
        1
    )

# 8. Mostrar resumen
total = len(plazas)
ocupadas = len(plazas_ocupadas)
disponibles = total - ocupadas

print("\nESTADO DEL PARQUEADERO")
print("----------------------")
print(f"Total de plazas: {total}")
print(f"Plazas ocupadas: {ocupadas}")
print(f"Plazas disponibles: {disponibles}")

# 9. Mostrar resultado
cv2.imshow(
    "Clasificacion de plazas",
    imagen_resultado
)

cv2.waitKey(0)
cv2.destroyAllWindows()
