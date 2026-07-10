from tools import sumar, contar_palabras

print(sumar(10, 5))
print(contar_palabras("Python para agentes de IA"))

with open("data/notas.txt", "r", encoding="utf-8") as archivo:
    contenido = archivo.read()

print(contenido)


respuesta = "Resumen generado por el agente"

with open("data/respuesta.txt", "w", encoding="utf-8") as archivo:
    archivo.write(respuesta)


import json

estudiante = {
    "nombre": "Ana",
    "curso": "IA",
    "progreso": 0.75
}

with open("data/estudiante.json", "w", encoding="utf-8") as archivo:
    json.dump(estudiante, archivo, ensure_ascii=False, indent=2)
    
with open("data/estudiante.json", "r", encoding="utf-8") as archivo:
    datos = json.load(archivo)

print(datos["nombre"])