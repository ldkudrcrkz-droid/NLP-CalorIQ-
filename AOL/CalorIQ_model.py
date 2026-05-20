import pickle
import numpy as np
import os
import ast
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, util

app = FastAPI()

# Konfigurasi CORS agar React Frontend bisa mengakses API lintas port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Skema Request Data dari Frontend
class ProfileInput(BaseModel):
    gender: str
    age: int
    weight: float
    height: float

class RecommendationRequest(BaseModel):
    profile: ProfileInput
    query: str

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PKL_PATH = os.path.join(BASE_DIR, "recipes_embedded.pkl")

print("Memuat model SBERT...")
model = SentenceTransformer('all-MiniLM-L6-v2')

print(f"Memuat database resep dari: {PKL_PATH}...")
try:
    with open(PKL_PATH, "rb") as f:
        data_load = pickle.load(f)
    df = data_load["dataframe"]
    corpus_embeddings = data_load["embeddings"]
    print("Sistem AI CalorIQ Siap Digunakan!")
except FileNotFoundError:
    print(f"\n[ERROR] File '{PKL_PATH}' belum dibuat! Jalankan build_embeddings.py terlebih dahulu.\n")

@app.post("/api/recommend")
async def recommend_recipe(request: RecommendationRequest):
    try:
        user_query = request.query
        user_profile = request.profile
        
        # Kalkulasi BMR harian pengguna (Rumus Harris-Benedict)
        if user_profile.gender == 'male':
            bmr = round(88.362 + (13.397 * user_profile.weight) + (4.799 * user_profile.height) - (5.677 * user_profile.age))
        else:
            bmr = round(447.593 + (9.247 * user_profile.weight) + (3.098 * user_profile.height) - (4.330 * user_profile.age))
            
        height_m = user_profile.height / 100
        bmi = round(user_profile.weight / (height_m ** 2), 1)

        # Kalkulasi Cosine Similarity teks query dengan dataset resep
        query_embedding = model.encode(user_query, convert_to_tensor=True)
        cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0].cpu().numpy()
        
        # Batasi kalori rekomendasi per porsi sebesar maksimal 40% dari total BMR harian
        max_calories_per_meal = bmr * 0.40
        
        recipes_response = []
        sorted_indices = np.argsort(cos_scores)[::-1]
        
        for idx in sorted_indices:
            if len(recipes_response) >= 3:
                break
                
            row = df.iloc[int(idx)]
            
            # Parsing array string nutrition bawaan dataset Food.com:
            # [calories, total_fat, sugar, sodium, protein, saturated_fat, carbs]
            nutrition_str = row.get('nutrition', '[0, 0, 0, 0, 0, 0, 0]')
            try:
                nutrition_list = ast.literal_eval(nutrition_str)
            except:
                nutrition_list = [0, 0, 0, 0, 0, 0, 0]
                
            recipe_calories = float(nutrition_list[0])
            
            # Jalankan filter kalori porsi
            if recipe_calories > max_calories_per_meal:
                continue
            
            # Mengubah format %DV dari dataset menjadi estimasi gram (g) untuk UI
            fat_gram = round((float(nutrition_list[1]) / 100) * 65)
            protein_gram = round((float(nutrition_list[4]) / 100) * 50)
            carbs_gram = round((float(nutrition_list[6]) / 100) * 300)
            
            # Ekstraksi petunjuk pengerjaan (steps)
            steps_data = row.get('steps', "[]")
            if isinstance(steps_data, str) and steps_data.startswith('['):
                try: steps_data = ast.literal_eval(steps_data)
                except: steps_data = [steps_data]

            recipes_response.append({
                "id": str(row.get('id', idx)),
                "name": str(row.get('name', 'Healthy Meal')).title(),
                "description": str(row.get('description', 'Tasty choice for your diet.')) if str(row.get('description')) != 'nan' else 'Healthy home-cooked recipe.',
                "imageUrl": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500",
                "prepTime": int(row.get('minutes', 25)),
                "servings": 1,
                "calories": int(recipe_calories),
                "protein": protein_gram,
                "fat": fat_gram,
                "carbs": carbs_gram,
                "steps": steps_data if isinstance(steps_data, list) else [str(steps_data)]
            })
            
        # Fallback jika tidak ditemukan resep yang lolos filter kalori ketat
        if not recipes_response:
            for idx in sorted_indices[:3]:
                row = df.iloc[int(idx)]
                nutrition_list = ast.literal_eval(row.get('nutrition', '[300, 0, 0, 0, 15, 0, 25]'))
                steps_data = row.get('steps', "[]")
                if isinstance(steps_data, str) and steps_data.startswith('['):
                    try: steps_data = ast.literal_eval(steps_data)
                    except: steps_data = [steps_data]
                    
                recipes_response.append({
                    "id": str(row.get('id', idx)),
                    "name": str(row.get('name', 'Diet Menu')).title(),
                    "description": "Selected menu for basic balanced nutrition.",
                    "imageUrl": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500",
                    "prepTime": int(row.get('minutes', 20)),
                    "servings": 1,
                    "calories": int(float(nutrition_list[0])),
                    "protein": round((float(nutrition_list[4]) / 100) * 50),
                    "fat": round((float(nutrition_list[1]) / 100) * 65),
                    "carbs": round((float(nutrition_list[6]) / 100) * 300),
                    "steps": steps_data if isinstance(steps_data, list) else [str(steps_data)]
                })

        return {
            "content": f"Berdasarkan profil kesehatan Anda (BMI: {bmi} | Target porsi ideal: <{int(max_calories_per_meal)} Kalori), berikut adalah menu sehat untuk pencarian '{user_query}':",
            "recipes": recipes_response
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))