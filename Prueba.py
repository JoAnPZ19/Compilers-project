### PRUEBAS
def random_operation(a, b):
    c = a + b

    # Hi I'm a comment!
    return c + a * b + 2.6548

def hola(a,b):
    return a + b

print(hola(1,2))

def fib(n):
    if n == 1 or n == 2:
        return 1
    else:
        return fib(n-1) + fib(n-2)
    print("Hola, dentro de fib()")

print (fib(5))


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
    print(fib(b-5))
    c = b
    b = "hola"
    b=c-2
print("Si printeo mis probabilidades de graduarme suben :)")
