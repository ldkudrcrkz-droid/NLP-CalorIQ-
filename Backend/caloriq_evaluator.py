"""
CalorIQ Evaluation Module
=========================
Pasang di atas CalorIQ_model.py (atau import terpisah).
Jalankan: python caloriq_evaluator.py
"""

import pandas as pd
import numpy as np
from sentence_transformers import util
import re



def score_retrieval(rec_system, query: str, results: pd.DataFrame) -> dict:
    """
    Hitung cosine similarity antara query dan setiap hasil rekomendasi.
    Kembalikan mean, min, max.
    """
    query_emb = rec_system.model.encode(query, convert_to_tensor=True)
    result_embs = rec_system.model.encode(
        results['combined'].tolist(), convert_to_tensor=True
    )
    sims = util.cos_sim(query_emb, result_embs)[0].cpu().numpy()

    return {
        "cosine_mean":  float(np.mean(sims)),
        "cosine_min":   float(np.min(sims)),
        "cosine_max":   float(np.max(sims)),
        "scores":       sims.tolist()
    }



def ndcg_at_k(scores: list, k: int = 5) -> float:
    """
    Hitung NDCG@k menggunakan cosine similarity sebagai relevance proxy.
    Skor dinormalisasi ke [0,1] secara otomatis karena cosine sudah dalam [-1,1].
    """
    scores = np.array(scores[:k])
    dcg  = np.sum(scores / np.log2(np.arange(2, len(scores) + 2)))
    idcg = np.sum(np.sort(scores)[::-1] / np.log2(np.arange(2, len(scores) + 2)))
    return float(dcg / idcg) if idcg > 0 else 0.0



def score_nutrition(results: pd.DataFrame, meal_target: float) -> dict:
    """
    Evaluasi kesesuaian nutrisi hasil rekomendasi terhadap target kalori.
    Dihitung berdasarkan rata-rata opsi menu alternatif yang disodorkan sistem.
    """
    if results.empty:
        return {
            "total_calories": 0.0,
            "meal_target": round(meal_target, 2),
            "calorie_gap": round(meal_target, 2),
            "calorie_accuracy": 0.0,
            "fits_target": False,
            "avg_protein_g": 0.0,
            "avg_fat_g": 0.0,
        }


    avg_cal     = results['calories'].mean() 
    calorie_gap = abs(avg_cal - meal_target)
    
   
    fit         = avg_cal <= meal_target

    avg_protein = results['protein'].mean()
    avg_fat     = results['fat'].mean()

    
    cal_accuracy = max(0.0, 1.0 - (calorie_gap / meal_target))

    return {
        "total_calories":   round(avg_cal, 2),
        "meal_target":      round(meal_target, 2),
        "calorie_gap":      round(calorie_gap, 2),
        "calorie_accuracy": round(cal_accuracy, 4),
        "fits_target":      fit,
        "avg_protein_g":    round(avg_protein, 2),
        "avg_fat_g":        round(avg_fat, 2),
    }


def precision_at_k(scores: list, threshold: float = 0.25, k: int = 5) -> float:
    """
    Berapa banyak dari top-k hasil yang memiliki cosine similarity >= threshold?
    Threshold 0.25 cukup konservatif untuk all-MiniLM-L6-v2.
    """
    relevant = sum(1 for s in scores[:k] if s >= threshold)
    return round(relevant / min(k, len(scores)), 4)



def score_system(query: str, results: pd.DataFrame, entities: dict) -> dict:
    """
    Evaluasi kualitas entity extraction dan fallback coverage.
    """
    all_entities = (
        entities.get("protein", []) +
        entities.get("carb", []) +
        entities.get("dish", [])
    )
    used_fallback = len(all_entities) == 0

    
    hit_count = 0
    if all_entities and not results.empty:
        combined_text = " ".join(results['combined'].tolist())
        for ent in all_entities:
            if ent.lower() in combined_text:
                hit_count += 1
        entity_hit_rate = hit_count / len(all_entities)
    else:
        entity_hit_rate = 0.0

    return {
        "entities_found":    all_entities,
        "used_fallback":     used_fallback,
        "entity_hit_rate":   round(entity_hit_rate, 4),
    }



def evaluate(rec_system, bot, profile: dict, query: str, k: int = 5) -> dict:
    """
    Jalankan semua metrik sekaligus untuk satu query.

    Contoh:
        profile = {"gender": "male", "age": 25, "weight": 70, "height": 175}
        query   = "high protein chicken steak low fat"
        results = evaluate(rec_system, bot, profile, query)
        print(results)
    """
    from CalorIQ_model import extract_entities  

    
    bmi      = profile['weight'] / ((profile['height'] / 100) ** 2)
    bmr      = 10 * profile['weight'] + 6.25 * profile['height'] - 5 * profile['age'] + 5
    meal_target = bmr * 1.2 * 0.3

    
    constraints = {"low_fat": "low fat" in query.lower()}
    entities    = extract_entities(query)
    results     = rec_system.search(query, constraints, top_n=k)

    
    retrieval   = score_retrieval(rec_system, query, results)
    nutrition   = score_nutrition(results, meal_target)
    system      = score_system(query, results, entities)

    ndcg        = ndcg_at_k(retrieval["scores"], k=k)
    precision   = precision_at_k(retrieval["scores"], threshold=0.25, k=k)

    
    composite = round(
        0.4 * retrieval["cosine_mean"] +
        0.3 * nutrition["calorie_accuracy"] +
        0.2 * precision +
        0.1 * system["entity_hit_rate"],
        4
    )

    return {
        "query":          query,
        "bmi":            round(bmi, 2),
        "meal_target":    round(meal_target, 2),
        "retrieval":      retrieval,
        "ndcg_at_k":      ndcg,
        "precision_at_k": precision,
        "nutrition":      nutrition,
        "system":         system,
        "composite_score": composite,
        "top_results":    results[['name', 'calories', 'protein', 'fat']].to_dict(orient='records')
    }



def batch_evaluate(rec_system, bot, profile: dict, queries: list) -> pd.DataFrame:
    
    rows = []
    for q in queries:
        try:
            result = evaluate(rec_system, bot, profile, q)
            rows.append({
                "query":              result["query"],
                "composite_score":    result["composite_score"],
                "cosine_mean":        result["retrieval"]["cosine_mean"],
                "ndcg_at_k":          result["ndcg_at_k"],
                "precision_at_k":     result["precision_at_k"],
                "calorie_accuracy":   result["nutrition"]["calorie_accuracy"],
                "fits_target":        result["nutrition"]["fits_target"],
                "entity_hit_rate":    result["system"]["entity_hit_rate"],
                "used_fallback":      result["system"]["used_fallback"],
            })
        except Exception as e:
            rows.append({"query": q, "error": str(e)})

    return pd.DataFrame(rows)



if __name__ == "__main__":
    from CalorIQ_model import load_or_preprocess, SBERTRecommender, CalorIQBot

    df       = load_or_preprocess("RAW_recipes.csv")
    rec      = SBERTRecommender()
    rec.fit(df)
    bot      = CalorIQBot(rec)

    profile  = {"gender": "male", "age": 25, "weight": 70, "height": 175}

    test_queries = [
        "chicken steak high protein",
        "low fat salmon with rice",
        "beef stew soup",
        "pasta carbonara",
        "healthy breakfast low fat",
    ]

    print("\n========= SINGLE QUERY EVALUATION =========")
    result = evaluate(rec, bot, profile, test_queries[0])
    print(f"Query         : {result['query']}")
    print(f"Composite     : {result['composite_score']}")
    print(f"NDCG@5        : {result['ndcg_at_k']}")
    print(f"Precision@5   : {result['precision_at_k']}")
    print(f"Cosine Mean   : {result['retrieval']['cosine_mean']:.4f}")
    print(f"Calorie Acc   : {result['nutrition']['calorie_accuracy']:.4f}")
    print(f"Fits Target   : {result['nutrition']['fits_target']}")
    print(f"Entity Hits   : {result['system']['entity_hit_rate']:.2f}")
    print(f"Top Results   :")
    for r in result['top_results']:
        print(f"  - {r['name']} | {r['calories']} kcal | P:{r['protein']}g | F:{r['fat']}g")

    print("\n========= BATCH EVALUATION =========")
    df_eval = batch_evaluate(rec, bot, profile, test_queries)
    print(df_eval.to_string(index=False))

    print("\n========= AGGREGATE STATS =========")
    numeric_cols = ["composite_score", "cosine_mean", "ndcg_at_k",
                    "precision_at_k", "calorie_accuracy", "entity_hit_rate"]
    print(df_eval[numeric_cols].describe().round(4).to_string())
