import random

# Lista para almacenar los 10 arreglos generados
arreglos_aleatorios = []

# Generar 10 arreglos
for i in range(10):
    # 1. Determinar la cantidad de números (entre 5 y 100)
    cantidad_numeros = random.randint(5, 100)

    # 2. Crear el arreglo con números aleatorios entre 1 y 2000
    #    La expresión genera 'cantidad_numeros' números.
    arreglo = [random.randint(1, 2000) for _ in range(cantidad_numeros)]

    # 3. Agregar el arreglo a la lista principal
    arreglos_aleatorios.append(arreglo)

# Imprimir los resultados (solo mostramos el primer elemento de cada arreglo para ahorrar espacio)
print("Se han generado 10 arreglos (listas) de números aleatorios.")
print("-" * 50)

for j, arreglo in enumerate(arreglos_aleatorios):
    # Mostramos la longitud del arreglo
    longitud = len(arreglo)
    # Mostramos los primeros 5 elementos como ejemplo
    ejemplo = arreglo[:5]
    print(f"**Arreglo {j+1}:**")
    print(f"  - Cantidad de números: **{longitud}**")
    print(f"  - Primeros 5 números: {ejemplo}...")
    # Si desea ver el arreglo completo, descomente la siguiente línea:
    # print(f"  - Arreglo completo: {arreglo}")
    print("-" * 50)

# Definimos una función para generar un arreglo individual
def generar_arreglo_aleatorio():
    """Genera un arreglo con una longitud aleatoria (5-100) y números aleatorios (1-2000)."""
    cantidad = random.randint(5, 50)
    arreglo = [random.randint(1, 2000) for _ in range(cantidad)]
    return arreglo

# Generamos los 10 arreglos
arreglo_1 = generar_arreglo_aleatorio()
arreglo_2 = generar_arreglo_aleatorio()
arreglo_3 = generar_arreglo_aleatorio()
arreglo_4 = generar_arreglo_aleatorio()
arreglo_5 = generar_arreglo_aleatorio()
arreglo_6 = generar_arreglo_aleatorio()
arreglo_7 = generar_arreglo_aleatorio()
arreglo_8 = generar_arreglo_aleatorio()
arreglo_9 = generar_arreglo_aleatorio()
arreglo_10 = generar_arreglo_aleatorio()

# --- Impresión de resumen para verificar ---
print("✅ ¡Arreglos generados!")
print("\n**Resumen de Longitudes:**")
print(arreglo_1)
print(arreglo_2)
print(arreglo_3)
print(arreglo_4)
print(arreglo_5)
print(arreglo_6)
print(arreglo_7)
print(arreglo_8)
print(arreglo_9)
print(arreglo_10)
