
import cv2
import subprocess
import sys

VIDEO_URL = "https://youtu.be/gQUoJ6inXK4"

def get_stream_url():
    print("Obteniendo direccion de transmision...")

    result = subprocess.run(
        [
            sys.executable, "-m", "yt_dlp",
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


def main():
    stream_url = get_stream_url()

    if not stream_url:
        return

    print("Conectando con la camara...")

    camera = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)

    if not camera.isOpened():
        print("No se pudo establecer la conexion.")
        return

    print("Conexion establecida.")

    while True:
        success, frame = camera.read()

        if not success:
            print("No se pudo recibir el fotograma.")
            break

        cv2.imshow("Parqueadero Inteligente", frame)
        cv2.imwrite("captura_parqueadero.jpg", frame)
        
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
