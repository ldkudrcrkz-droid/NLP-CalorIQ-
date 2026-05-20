
import pandas as pd
import numpy as np
import re
import ast
import os
import pickle

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

def parse_nutrition(text):
    try:
        values = ast.literal_eval(text)
        return {
            "calories": values[0],
            "fat": values[1],
            "protein": values[4]
        }
    except:
        return {"calories": np.nan, "fat": np.nan, "protein": np.nan}

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

    # REMOVE EXTREME OUTLIERS
    df = df[
        (df['calories'] > 50) & (df['calories'] < 800) &
        (df['protein'] < 100) &
        (df['fat'] < 60)
    ]

    df = df[['name', 'combined', 'calories', 'protein', 'fat', 'steps_clean']]

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

        self.df = df

        if os.path.exists("embeddings_full.pkl"):
            print("⚡ Loading embeddings...")
            with open("embeddings_full.pkl", "rb") as f:
                self.embeddings = pickle.load(f)
        else:
            print("⏳ Encoding recipes (once)...")
            self.embeddings = self.model.encode(
                df['combined'].tolist(),
                convert_to_tensor=True,
                show_progress_bar=True
            )
            with open("embeddings_full.pkl", "wb") as f:
                pickle.dump(self.embeddings, f)

    def search(self, query, constraints, include_words=None, top_n=5):

        df = self.df.copy()
        emb = self.embeddings

        # 🔥 STRICT FILTER
        if include_words:
            for w in include_words:
                mask = df['combined'].str.contains(w, na=False)
                if mask.sum() > 0:
                    df = df[mask]
                    emb = emb[mask.values]

        # SBERT similarity
        query_emb = self.model.encode(query, convert_to_tensor=True)
        scores = util.cos_sim(query_emb, emb)[0].cpu().numpy()

        df['score'] = scores

        # NUTRITION FILTER
        if constraints["low_fat"]:
            df = df[df['fat'] < 20]

        df = df[df['calories'] < 600]

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
            main = self.rec.search(
                query,
                constraints,
                include_words=entities["protein"] + entities["dish"]
            ).head(1)

        # ===== SIDE DISH =====
        side = None
        if entities["carb"]:
            side = self.rec.search(
                query,
                constraints,
                include_words=entities["carb"]
            ).head(1)

        recs = pd.concat([main, side]).drop_duplicates()

        # fallback kalau kosong
        if recs.empty:
            recs = self.rec.search(query, constraints).head(2)

        total_cal = recs['calories'].sum()

        # =========================
        # RESPONSE
        # =========================
        response = f"""
🍽️ Personalized Recommendation

Query: "{query}"

📊 BMI: {bmi:.2f}
🔥 Target per meal: {meal_target:.0f} kcal
"""

        for _, r in recs.iterrows():

            steps = re.split(r'\.\s+|,\s+', r['steps_clean'])

            response += f"""
--------------------------------
🍽️ {r['name']}
Calories: {r['calories']:.1f} kcal | Protein: {r['protein']:.1f} g

Steps:
"""

            count = 0
            for s in steps:
                if len(s.strip()) > 20:
                    count += 1
                    response += f"{count}. {s.strip().capitalize()}\n"
                if count == 5:
                    break

        response += f"\n👉 Total calories: {total_cal:.1f} kcal\n"

        if total_cal <= meal_target:
            response += "✅ Fits your nutritional needs\n"
        else:
            response += "⚠️ Above recommended calories\n"

        response += "💡 Tip: Use less oil & prefer grilling."

        return response

# =========================
# MAIN
# =========================
if __name__ == "__main__":

    df = load_or_preprocess("RAW_recipes.csv")

    rec = SBERTRecommender()
    rec.fit(df)

    bot = CalorIQBot(rec)

    user = {
        "gender": "male",
        "age": 20,
        "weight": 65,
        "height": 165
    }

    query = "I want chicken steak with mashed potato low fat"

    print(bot.generate(user, query))

