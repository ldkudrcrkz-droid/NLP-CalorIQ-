import pandas as pd
import pickle
import os
from sentence_transformers import SentenceTransformer

def main():
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CSV_PATH = os.path.join(BASE_DIR, "RAW_recipes.csv")
    PKL_PATH = os.path.join(BASE_DIR, "recipes_embedded.pkl")

    print(f"1. Membaca dataset resep dari: {CSV_PATH}...")
    if not os.path.exists(CSV_PATH):
        print(f"[ERROR] File '{CSV_PATH}' tidak ditemukan. Pastikan file berada di folder AOL!")
        return
        
    df = pd.read_csv(CSV_PATH) 

    
    print("   Membatasi dataset ke 15.000 baris pertama untuk optimasi...")
    df = df.head(15000).copy()

    print("2. Menyiapkan teks gabungan untuk embedding...")
    
    df['name'] = df['name'].fillna('')
    df['description'] = df['description'].fillna('')
    
    
    df['text_for_embedding'] = "Recipe Name: " + df['name'] + ". Description: " + df['description']

    print("3. Memuat model SentenceTransformer (SBERT)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print("4. Memproses matriks embedding (Tunggu hingga progress bar 100%)...")
    corpus_sentences = df['text_for_embedding'].astype(str).tolist()
    corpus_embeddings = model.encode(corpus_sentences, show_progress_bar=True)

    print(f"5. Menyimpan hasil dataframe dan embedding ke: {PKL_PATH}...")
    dataset_matang = {
        "dataframe": df,
        "embeddings": corpus_embeddings
    }

    with open(PKL_PATH, "wb") as f:
        pickle.dump(dataset_matang, f)

    print("\n[SUKSES] File 'recipes_embedded.pkl' berhasil dibuat!")
    print("Sekarang Anda bisa menjalankan server FastAPI utama secara instan.")

if __name__ == "__main__":
    main()