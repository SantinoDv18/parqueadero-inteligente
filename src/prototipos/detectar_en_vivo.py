
import cv2
import subprocess
import sys
from ultralytics import YOLO

# 1. Configuracion de la camara
VIDEO_URL = "https://youtu.be/gQUoJ6inXK4"

# 2. Cargar el modelo YOLO
print("Cargando modelo YOLO...")
model = YOLO("yolo11n.pt")


# 3. Obtener la direccion de la transmision
def get_stream_url():

    print("Obteniendo direccion de la transmision...")

    result = subprocess.run(
        [
            sys.executable,
            "-m", "yt_dlp",
            "-f", "230",
            "-g",
            "--no-warnings",
            "--no-playlist",
            VIDEO_URL
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(result.stderr)
        return None

    urls = result.stdout.strip().splitlines()

    if not urls:
        return None

    return urls[0]


# 4. Funcion principal
def main():

    stream_url = get_stream_url()

    if not stream_url:
        print("No se pudo obtener la transmision.")
        return

    # Conectar con la camara
    camera = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)

    if not camera.isOpened():
        print("No se pudo conectar con la camara.")
        return

    print("Camara conectada correctamente.")
    print("Iniciando deteccion de vehiculos...")

    # Coordenadas de nuestra zona
    x_inicio = 305
    y_inicio = 85

    x_final = 570
    y_final = 235

    try:

        while True:

            # Obtener fotograma
            success, frame = camera.read()

            if not success:
                print("No se pudo recibir el fotograma.")
                break

            # Comprobar dimensiones
            alto, ancho = frame.shape[:2]

            if x_final > ancho or y_final > alto:
                print("Coordenadas fuera de la imagen.")
                break

            # Copiar imagen original
            frame_original = frame.copy()

            # Recortar zona de interes
            zona = frame[
                y_inicio:y_final,
                x_inicio:x_final
            ]

            # Ejecutar YOLO
            result = model.predict(
                source=zona,
                conf=0.50,
                imgsz=640,
                classes=[2, 3, 5, 7],
                iou=0.45,
                verbose=False
            )[0]

            # Dibujar detecciones
            zona_detectada = result.plot(
                line_width=1,
                font_size=8
            )

            # Dibujar rectangulo en imagen original
            cv2.rectangle(
                frame_original,
                (x_inicio, y_inicio),
                (x_final, y_final),
                (0, 255, 0),
                2
            )

            # Mostrar cantidad de detecciones
            cantidad = len(result.boxes)

            cv2.putText(
                zona_detectada,
                f"Vehiculos: {cantidad}",
                (5, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1
            )

            # Mostrar ventanas
            cv2.imshow(
                "Camara original",
                frame_original
            )

            cv2.imshow(
                "Deteccion YOLO en vivo",
                zona_detectada
            )

            # Salir presionando Q
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:

        camera.release()
        cv2.destroyAllWindows()

        print("Deteccion finalizada.")


if __name__ == "__main__":
    main()
