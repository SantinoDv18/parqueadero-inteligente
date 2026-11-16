# Datos propios: Talatshii Outlet Plaza (Riohacha)

Esta carpeta contiene los datos de la escena propia. Los videos NO se suben a GitHub (pesan decenas de MB y
muestran placas y personas): estan en la carpeta compartida de Drive, enlace en el README principal.

Archivos que van aqui:

| Archivo | Que es | Como se genera |
|---|---|---|
| `plazas.json` | Los 9 cupos (poligonos) dibujados sobre el video propio | `src/herramientas/definir_plazas.py` |
| `zona_parqueadero.jpg` | Fotograma de referencia sobre el que se dibujaron los cupos | `--ref-frame` del sistema |
| `pruebas/frame_XXXXX.jpg` | 12 fotogramas de prueba equidistantes del video | `--exportar 12` |
| `gt.json` | Etiquetas reales (1 = ocupado, 0 = libre) por fotograma y cupo | `src/etiquetar_gt.py` |

Videos originales (en Drive): 32 s (video principal), 12 s (vista cenital cercana) y 147 s (vertical, muy cercano).
