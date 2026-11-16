
from ultralytics import YOLO
import cv2

# 1. Cargar el modelo YOLO
print("Cargando modelo YOLO...")

model = YOLO("yolo11n.pt")

# 2. Ejecutar la deteccion sobre nuestra zona
print("Analizando imagen...")

results = model.predict(
    source="zona_parqueadero.jpg",
    conf=0.50,
    imgsz=640,
    classes=[2, 3, 5, 7],
    verbose=False
)

# 3. Obtener el resultado
result = results[0]

# 4. Dibujar los resultados sobre la imagen
imagen_resultado = result.plot(
    line_width=1,
    font_size=8
)

# 5. Guardar la imagen
cv2.imwrite(
    "vehiculos_detectados.jpg",
    imagen_resultado
)

# 6. Mostrar el resultado
cv2.imshow(
    "Deteccion de vehiculos",
    imagen_resultado
)

# 7. Mostrar informacion de las detecciones
print("\nVehiculos detectados:")

if result.boxes is not None:
    for box in result.boxes:
        clase_id = int(box.cls[0])
        confianza = float(box.conf[0])

        nombre = model.names[clase_id]

        print(
            f"Vehiculo: {nombre} | "
            f"Confianza: {confianza:.2f}"
        )

    print(f"\nTotal detectado: {len(result.boxes)}")

# 8. Esperar una tecla
cv2.waitKey(0)
cv2.destroyAllWindows()
