
import cv2
import subprocess
import sys

# 1. Direccion de la transmision
VIDEO_URL = "https://youtu.be/gQUoJ6inXK4"


# 2. Obtener la direccion real del video
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
        print("Error al obtener el video:")
        print(result.stderr)
        return None

    urls = result.stdout.strip().splitlines()

    if not urls:
        print("No se obtuvo ninguna direccion.")
        return None

    return urls[0]


# 3. Funcion principal
def main():

    # Obtener la direccion de la transmision
    stream_url = get_stream_url()

    if not stream_url:
        return

    print("Conectando con la camara...")

    # Conectar OpenCV con la transmision
    camera = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)

    if not camera.isOpened():
        print("No se pudo establecer la conexion.")
        return

    print("Conexion establecida correctamente.")

    # 4. Definir las coordenadas de nuestra zona
    x_inicio = 305
    y_inicio = 85

    x_final = 570
    y_final = 235

    # 5. Procesar los fotogramas continuamente
    while True:

        success, frame = camera.read()

        if not success:
            print("No se pudo recibir el fotograma.")
            break

        # Obtener dimensiones del fotograma
        alto, ancho = frame.shape[:2]

        # Comprobar que las coordenadas sean validas
        if x_final > ancho or y_final > alto:
            print("Las coordenadas exceden el tamano del video.")
            break

        # Crear una copia para dibujar el rectangulo
        frame_original = frame.copy()

        # Dibujar la zona seleccionada
        cv2.rectangle(
            frame_original,
            (x_inicio, y_inicio),
            (x_final, y_final),
            (0, 255, 0),
            2
        )

        # 6. Recortar la zona de interes
        zona = frame[
            y_inicio:y_final,
            x_inicio:x_final
        ]

        # 7. Mostrar las dos ventanas
        cv2.imshow("Camara original", frame_original)

        cv2.imshow("Zona de analisis", zona)

        # Presionar Q para finalizar
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # 8. Liberar recursos
    camera.release()
    cv2.destroyAllWindows()

    print("Programa finalizado.")


if __name__ == "__main__":
    main()
