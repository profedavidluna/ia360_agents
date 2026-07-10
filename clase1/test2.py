def saludar(nombre):
    return "Hola, " + nombre

def calcular_iva(monto, porcentaje=0.13):
    iva = monto * porcentaje
    total = monto + iva
    return total

def resumir_notas(notas):
    promedio = sum(notas) / len(notas)
    maxima = max(notas)
    minima = min(notas)

    if promedio >= 70:
        estado = "aprobado"
    else:
        estado = "reforzar"

    return {
        "promedio": promedio,
        "maxima": maxima,
        "minima": minima,
        "estado": estado
    }

print(calcular_iva(1000))

mensaje = saludar("Luis")
print(mensaje)

print(resumir_notas([85, 90, 72, 68]))