import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List
import os

# Definir la ruta del archivo CSV
resultado_crew_path = os.path.join(os.path.dirname(__file__), 'resultado_crew.csv')
funcion_director_path = os.path.join(os.path.dirname(__file__), 'FuncionDirector.csv')

app = FastAPI()

# Cargar los datasets
try:
    resultado_crew = pd.read_csv(resultado_crew_path)
    funcion_director = pd.read_csv(funcion_director_path)
except FileNotFoundError as e:
    raise HTTPException(status_code=500, detail=f"Error al cargar los archivos: {str(e)}")

# Modelo para la información de la película
class MovieInfo(BaseModel):
    title: str
    release_date: str
    return_: str  # Retorno como porcentaje
    budget: str   # Presupuesto formateado
    revenue: str  # Ingresos formateados

# Modelo para la respuesta del director
class DirectorResponse(BaseModel):
    director_name: str
    total_revenue: str  # Ingresos totales formateados
    movies: List[MovieInfo]

# Mensaje de bienvenida
@app.get("/", tags=["Bienvenida"])
def welcome(request: Request):
    # Obtener la URL base dinámicamente
    base_url = str(request.base_url)  # Obtiene la URL base

    return {
        "message": "Bienvenido a la API de Información de Directores de Cine.",
        "functions": {
            f"{base_url}/director/{{director_name}}": "Obtiene información sobre un director específico, incluyendo sus películas y ingresos totales.",
            f"{base_url}/directores": "Devuelve una lista de todos los directores disponibles en la base de datos."
        },
        "examples": {
            "Get Director Info": f"Ejemplo: {base_url}/director/Steven%20Spielberg",
            "Get All Directors": f"Ejemplo: {base_url}/directores"
        }
    }

@app.get("/director/{director_name}", response_model=DirectorResponse)
def get_director_info(director_name: str):
    # Normalizar el nombre del director a minúsculas
    director_name_lower = director_name.lower()

    # Filtrar las películas del director sin discriminar mayúsculas
    director_movies = resultado_crew[resultado_crew['name'].str.lower() == director_name_lower]

    if director_movies.empty:
        raise HTTPException(status_code=404, detail="Director no encontrado")

    # Unir con el DataFrame de función del director para obtener más detalles
    director_movies = director_movies.merge(funcion_director, left_on='movie_id', right_on='id', how='inner')

    # Calcular ingresos totales
    total_revenue = director_movies['revenue'].sum()

    # Crear la lista de películas
    movies_info = [
        MovieInfo(
            title=row['title'],
            release_date=row['release_date'],
            return_=f"{row['return']:.2f}%",  # Formato de porcentaje
            budget=f"${row['budget']:,.2f}",   # Formato de moneda con separador de miles
            revenue=f"${row['revenue']:,.2f}"  # Formato de moneda con separador de miles
        ) for index, row in director_movies.iterrows()
    ]

    return DirectorResponse(
        director_name=director_name,
        total_revenue=f"${total_revenue:,.2f}",  # Formato de moneda con separador de miles
        movies=movies_info
    )

@app.get("/directores")
def obtener_directores():
    return resultado_crew['name'].unique().tolist()
