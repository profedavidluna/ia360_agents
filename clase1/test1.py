nombre = "Ana"
edad = 20
curso = "Inteligencia Artificial"

print(nombre)
print(edad)
print(curso)

edad = input("Ingrese su Edad: ")
edad = int(edad)

if edad >= 18:
    print("Puede usar la plataforma completa")
elif edad < 18 and edad >= 16:
    print("Puede usar la plataforma con restricciones")
else:
    print("Necesita autorización")

temas = ["Python", "APIs", "Agentes"]
temas.append("Machine Learning")
python_count = temas.count("Python")
print("Python aparece", python_count, "veces en la lista de temas")
for tema in temas:
    print("Estudiar:", tema)
    
intentos = 0
while intentos < 3:
    clave = input("Clave: ")
    if clave == "python":
        print("Acceso concedido")
        break
    intentos += 1
    
estudiante = {
    "nombre": "María",
    "curso": "IA",
    "activo": True
}

print(estudiante)
