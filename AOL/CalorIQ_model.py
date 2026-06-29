import pandas as pd
import numpy as np
import re
import ast
import os
import pickle
import traceback

from sentence_transformers import SentenceTransformer, util

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# nltk.download('stopwords')
# nltk.download('wordnet')

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

# =========================
# PREPROCESS
# =========================
def preprocess_text(text):
    text = str(text).lower()
    text = re.sub(r'[^a-zA-Z]', ' ', text)
    tokens = text.split()
    tokens = [lemmatizer.lemmatize(w) for w in tokens if w not in stop_words]
    return " ".join(tokens)

# =========================
# PARSING
# =========================
def parse_list_column(text):
    try:
        return " ".join(ast.literal_eval(text))
    except:
        return ""

def _parse_list_raw(text) -> list:
    """Parse list column menjadi list of strings (tidak di-preprocess, untuk tampilan)."""
    try:
        return ast.literal_eval(text)
    except:
        return []

def parse_nutrition(text):
    try:
        values = ast.literal_eval(text)
        return {
            "calories": values[0],
            "fat": values[1],
            "protein": values[4],
            "carbs": values[6] if len(values) > 6 else np.nan
        }
    except:
        return {"calories": np.nan, "fat": np.nan, "protein": np.nan, "carbs": np.nan}

# =========================
# LOAD DATA
# =========================
def load_or_preprocess(csv_path):

    cache_path = "cleaned_recipes_full.pkl"

    if os.path.exists(cache_path):
        print("⚡ Loading cleaned data...")
        return pd.read_pickle(cache_path)

    print("⏳ Preprocessing full dataset...")

    df = pd.read_csv(csv_path)

    df['steps_clean'] = df['steps'].apply(parse_list_column)
    df['tags_clean'] = df['tags'].apply(parse_list_column)

    nutrition_df = df['nutrition'].apply(parse_nutrition).apply(pd.Series)
    df = pd.concat([df, nutrition_df], axis=1)

    df['combined'] = (
        df['name'].fillna('') + " " +
        df['description'].fillna('') + " " +
        df['steps_clean'] + " " +
        df['tags_clean']
    )

    df['combined'] = df['combined'].apply(preprocess_text)

    # CLEAN
    df['calories'] = df['calories'].fillna(df['calories'].median())
    df['protein'] = df['protein'].fillna(0)
    df['fat'] = df['fat'].fillna(df['fat'].median())
    df['carbs'] = df['carbs'].fillna(df['carbs'].median()) if 'carbs' in df.columns else 0

    # REMOVE EXTREME OUTLIERS
    df = df[
        (df['calories'] > 50) & (df['calories'] < 800) &
        (df['protein'] < 100) &
        (df['fat'] < 60)
    ]

    # Simpan steps asli (readable) dan ingredients asli untuk ditampilkan di frontend
    df['steps_original'] = df['steps'].apply(lambda x: _parse_list_raw(x))
    df['ingredients_original'] = df['ingredients'].apply(lambda x: _parse_list_raw(x)) if 'ingredients' in df.columns else ''

    df = df[['name', 'combined', 'calories', 'protein', 'fat', 'carbs', 'steps_clean',
             'steps_original', 'ingredients_original']]

    df.to_pickle(cache_path)
    print("✅ Cached!")

    return df

# =========================
# ENTITY EXTRACTION
# =========================
def extract_entities(query):
    q = preprocess_text(query)

    protein_map = {
        "chicken": ["chicken"],
        "beef": ["beef", "steak"],
        "pork": ["pork"],
        "fish": ["fish", "salmon", "tuna"]
    }

    carb_map = {
        "potato": ["potato", "mashed potato"],
        "rice": ["rice"],
        "pasta": ["pasta"]
    }

    dish_map = {
        "steak": ["steak"],
        "soup": ["soup"],
        "stew": ["stew"]
    }

    def match(map_dict):
        result = []
        for key, vals in map_dict.items():
            for v in vals:
                if v in q:
                    result.append(key)
        return list(set(result))

    return {
        "protein": match(protein_map),
        "carb": match(carb_map),
        "dish": match(dish_map)
    }

# =========================
# SBERT RECOMMENDER
# =========================
class SBERTRecommender:

    def __init__(self):
        self.df = None
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embeddings = None

    def fit(self, df):
        self.df = df.reset_index(drop=True)

        if os.path.exists("embeddings_full.pkl"):
            print("⚡ Loading embeddings...")
            with open("embeddings_full.pkl", "rb") as f:
                self.embeddings = pickle.load(f)
        else:
            print("⏳ Encoding recipes (once)...")
            self.embeddings = self.model.encode(
                self.df['combined'].tolist(),
                convert_to_tensor=True,
                show_progress_bar=True
            )
            with open("embeddings_full.pkl", "wb") as f:
                pickle.dump(self.embeddings, f)

    def search(self, query, constraints, include_words=None, top_n=5, meal_target=None):
        df = self.df.copy()
        emb = self.embeddings

        # FIX: Filter dengan include_words menggunakan integer index agar aman
        if include_words:
            combined_mask = pd.Series([False] * len(df), index=df.index)
            for w in include_words:
                mask = df['combined'].str.contains(w, na=False)
                combined_mask = combined_mask | mask

            if combined_mask.sum() > 0:
                indices = combined_mask.index[combined_mask].tolist()
                df = df.loc[indices]
                if isinstance(emb, np.ndarray):
                    emb = emb[indices]
                else:
                    # tensor: convert ke numpy dulu agar indexing aman
                    emb = emb[indices]

        # SBERT Similarity Calculation
        query_emb = self.model.encode(query, convert_to_tensor=True)

        # FIX: Pastikan emb tidak kosong sebelum cos_sim
        if len(df) == 0:
            df = self.df.copy()
            emb = self.embeddings

        scores = util.cos_sim(query_emb, emb)[0].cpu().numpy()

        # FIX: Panjang scores harus sama dengan df
        if len(scores) != len(df):
            df = self.df.copy()
            emb = self.embeddings
            scores = util.cos_sim(query_emb, emb)[0].cpu().numpy()

        df = df.copy()
        df['score'] = scores

        # --- NUTRITION FILTERS ---
        if constraints.get("low_fat"):
            df = df[df['fat'] < 20]

        if meal_target is not None:
            df = df[df['calories'] <= meal_target]
        else:
            df = df[df['calories'] < 600]

        # Fallback jika filter terlalu ketat
        if df.empty:
            df = self.df.copy()
            scores_fallback = util.cos_sim(query_emb, self.embeddings)[0].cpu().numpy()
            df = df.copy()
            df['score'] = scores_fallback

        return df.sort_values("score", ascending=False).head(top_n)

# =========================
# CHATBOT
# =========================
class CalorIQBot:

    def __init__(self, rec):
        self.rec = rec

    def generate(self, profile, query):
        bmi = profile['weight'] / ((profile['height']/100)**2)
        bmr = 10*profile['weight'] + 6.25*profile['height'] - 5*profile['age'] + 5
        meal_target = bmr * 1.2 * 0.3

        constraints = {"low_fat": "low fat" in query.lower()}
        entities = extract_entities(query)

        # ===== MAIN DISH =====
        main = None
        if entities["protein"] and entities["dish"]:
            result = self.rec.search(
                query,
                constraints,
                include_words=entities["protein"] + entities["dish"],
                meal_target=meal_target
            )
            if not result.empty:
                main = result.head(1)

        # ===== SIDE DISH =====
        side = None
        if entities["carb"]:
            result = self.rec.search(
                query,
                constraints,
                include_words=entities["carb"],
                meal_target=meal_target
            )
            if not result.empty:
                side = result.head(1)

        parts = [x for x in [main, side] if x is not None and not x.empty]
        if parts:
            recs = pd.concat(parts).drop_duplicates()
        else:
            recs = pd.DataFrame()

        if recs.empty:
            recs = self.rec.search(query, constraints, meal_target=meal_target).head(5)

        if recs.empty:
            return {
                "message": "Maaf, tidak ditemukan rekomendasi yang sesuai. Coba kata kunci berbeda.",
                "recipes": []
            }

        total_cal = recs['calories'].sum()
        fits = total_cal <= meal_target

        # Build structured recipe list untuk frontend RecipeCard
        recipes = []
        for i, (_, r) in enumerate(recs.iterrows()):
            # Ambil steps asli (readable), fallback ke steps_clean jika tidak ada
            steps_raw = r.get('steps_original', [])
            if not isinstance(steps_raw, list) or len(steps_raw) == 0:
                # Fallback: split steps_clean
                steps_raw = [s.strip().capitalize() for s in
                             re.split(r'\.\s+|,\s+', str(r.get('steps_clean', '')))
                             if len(s.strip()) > 20][:5]

            ingredients_raw = r.get('ingredients_original', [])
            if not isinstance(ingredients_raw, list):
                ingredients_raw = []

            recipes.append({
                "id": str(i),
                "name": str(r['name']).title(),
                "description": f"A personalized recipe matching your query: {query}",
                "calories": round(float(r['calories']), 1),
                "protein": round(float(r['protein']), 1),
                "fat": round(float(r['fat']), 1),
                "carbs": round(float(r['carbs']), 1) if pd.notna(r.get('carbs', np.nan)) else 0,
                "ingredients": ingredients_raw[:10],  # max 10 bahan
                "steps": steps_raw[:6],               # max 6 langkah
            })

        # Summary message — naratif, menyebut nama resep secara eksplisit
        status = "fits your nutritional target" if fits else "Slightly above your recommended calories"
        message = self._build_narrative_message(recipes, query, status, bmi, meal_target, total_cal)

        return {"message": message, "recipes": recipes}

    def _build_narrative_message(self, recipes, query, status, bmi, meal_target, total_cal):
        """Susun kalimat pembuka yang naratif (menyebut nama resep), bukan template statis."""
        names = [r["name"] for r in recipes]

        if len(names) == 1:
            names_str = names[0]
        elif len(names) == 2:
            names_str = f"{names[0]} and {names[1]}"
        else:
            names_str = ", ".join(names[:-1]) + f", and {names[-1]}"

        openers = [
            "I've got just the thing for you",
            "Here's what I found that should hit the spot",
            "Take a look at these options",
        ]
        opener = openers[hash(query) % len(openers)]

        intro = (
            f"{opener} — some delicious options to help you reach your "
            f"\"{query}\" goal. "
            f"{names_str} {'are' if len(names) > 1 else 'is'} great picks that line up well with what you're after."
        )

        stats = (
            f"BMI: {bmi:.1f} | Meal target: {meal_target:.0f} kcal | "
            f"Total calories: {total_cal:.0f} kcal. {status}."
        )

        return f"{intro}\n\n{stats}"

# ==============================================================================
# 🚀 INITIALIZATION & FASTAPI API ROUTING
# ==============================================================================
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

print("📦 Initializing CalorIQ System...")
df_recipes = load_or_preprocess("RAW_recipes.csv")

rec_system = SBERTRecommender()
rec_system.fit(df_recipes)

bot = CalorIQBot(rec_system)
print("🚀 CalorIQ System is Ready!")

app = FastAPI(title="CalorIQ Recommendation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserProfile(BaseModel):
    gender: str
    age: int
    weight: float
    height: float

class ChatRequest(BaseModel):
    profile: UserProfile
    query: str

@app.post("/api/chat")
@app.post("/api/recommend")  # alias agar kompatibel dengan frontend lama
def chat_endpoint(payload: ChatRequest):
    try:
        user_profile_dict = {
            "gender": payload.profile.gender,
            "age": payload.profile.age,
            "weight": payload.profile.weight,
            "height": payload.profile.height
        }
        # bot.generate sekarang return dict: {"message": str, "recipes": list}
        result = bot.generate(user_profile_dict, payload.query)
        return {
            "response": result["message"],
            "recipes": result["recipes"]
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def index():
    return {"status": "online", "message": "CalorIQ Backend Engine is running smoothly."}