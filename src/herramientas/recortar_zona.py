
import cv2

# 1. Cargar la imagen de la camara
imagen = cv2.imread("captura_parqueadero.jpg")

# 2. Comprobar que la imagen se cargo correctamente
if imagen is None:
    print("Error: no se pudo cargar la imagen.")
    exit()

# 3. Definir las coordenadas de nuestra zona
x_inicio = 305
y_inicio = 85

x_final = 570
y_final = 235

# 4. Recortar la zona seleccionada
zona = imagen[y_inicio:y_final, x_inicio:x_final]

# Guardar la zona recortada en un archivo

cv2.imwrite("zona_parqueadero.jpg", zona)

# 5. Mostrar la zona recortada
cv2.imshow("Zona seleccionada", zona)

# 6. Esperar hasta que presionemos una tecla
cv2.waitKey(0)

# 7. Cerrar las ventanas
cv2.destroyAllWindows()
