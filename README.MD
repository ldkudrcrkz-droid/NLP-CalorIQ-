# CalorIQ - Personalized Recipe Chatbot

CalorIQ is an NLP-based chatbot that recommends personalized recipes based on:
- User profile (BMI, BMR)
- Nutritional constraints (low fat, high protein)
- Food preferences (e.g., chicken steak with mashed potato)

## Features
- Semantic search using SBERT
- Nutrition-aware filtering
- Multi-dish recommendation (main + side)
- Real-time chatbot response

## Model
- TF-IDF (baseline)
- Sentence-BERT (improved semantic search)

## Dataset
- Food.com Recipes dataset (Kaggle)
- File: `RAW_recipes.csv` — letakkan di dalam folder `Backend/`

## Project Structure

```
NLP-CalorIQ-/
├── Backend/               # Python FastAPI server
│   ├── CalorIQ_model.py   # Main backend file
│   ├── build_embeddings.py
│   └── caloriq_evaluator.py
├── Frontend/              # React source files
│   ├── app/
│   ├── main.tsx
│   └── styles/
├── package.json
└── vite.config.ts
```

## How to Run

Backend dan Frontend harus dijalankan **secara bersamaan di dua terminal terpisah**.

### Prerequisites

**Python dependencies (install sekali):**
```bash
pip install fastapi uvicorn sentence-transformers pandas numpy pydantic nltk
```

**Node dependencies (install sekali):**
```bash
cd NLP-CalorIQ-
npm install
```

---

### Terminal 1 — Backend

```bash
cd NLP-CalorIQ-/Backend
uvicorn CalorIQ_model:app --reload --host 127.0.0.1 --port 8000
```

Backend akan berjalan di: `http://127.0.0.1:8000`

> Saat pertama kali dijalankan, proses load dan preprocessing dataset membutuhkan waktu beberapa menit. Setelah selesai, akan muncul pesan `CalorIQ System is Ready!`

---

### Terminal 2 — Frontend

```bash
cd NLP-CalorIQ-
npm run dev
```

Frontend akan berjalan di: `http://localhost:5173`

Buka browser dan akses `http://localhost:5173`.

---

### Urutan yang Benar

1. Jalankan **Backend** terlebih dahulu (Terminal 1)
2. Tunggu hingga muncul `CalorIQ System is Ready!`
3. Baru jalankan **Frontend** (Terminal 2)
4. Buka browser di `http://localhost:5173`
