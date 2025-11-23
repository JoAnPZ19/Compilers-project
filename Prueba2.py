### PRUEBAS
x = -5

def random_operation(a, b):
    return a * b + 2.6548



def countdown(n):
    while n > 0:
        print(n)
        n = n - 1
    return "Done"

if x < 0:
    print("negative")
else:
    print("positive")

def fibonacci(n):
    if n == 1 or n == 2:
        return 1
    elif n == 0:
        return n / 0
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)