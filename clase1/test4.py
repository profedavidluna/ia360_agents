import requests

respuesta = requests.get("http://rickandmortyapi.com/api/character")
print(respuesta.status_code)
print(respuesta.json())