### PRUEBAS
def energy(mass, velocity):
    # It calculates kinetic energy
    print("Calculating energy...")
    return mass * velocity ** 2

mass = 70
v = 4.5
print("La energía calculada es: ", energy(mass, v))

def random_operation(a, b):
    print("Performing random operation with a and b...")
    c = a + b
    # Hi I'm a comment!
    return c + a * b + 2.6571896

def hola(a,b):
    return "Hola" + str(a) + str(b)

print(hola(1,2))

def Fibonacci(n):
    if n <= 0:
        return 0
    if n == 1 or n == 2:
        return 1
    else:
        return Fibonacci(n-1) + Fibonacci(n-2)

numeros = [0,1,2,3,4,5,6,7,8,9,10]
for num in numeros:
    print("Fibonacci de " + str(num) + " es " + str(Fibonacci(num)))

a = 4
print(a)
b = 5
a = "hola"
b = a + (str(b))
print(b)

a = [1, "hola", {"z": 1, "x": "ECCI"}, [1,2,3,4], (1,2,3,4)]
print(a)
print("Fibonacci")

for i in range(len(a)-1):
    print(a[i])
    
for e in a[3]:
    print (e)
    
a=5
b=10

while a < b:
    print(Fibonacci(b-5))
    b = b - 1

queene = True
jose = 789.298781
andrey = "ECCI"

print("Finalizado")
