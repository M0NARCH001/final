# app.py - Gradio space
import gradio as gr
import pandas as pd
from inference import score_candidates, load_artifact
import joblib, json

# Load foods master CSV (put Foods_Master.csv into the space repo)
FOODS_CSV = "Foods_Master.csv"
df_foods = pd.read_csv(FOODS_CSV).fillna(0.0)

def recommend_api(json_payload):
    """
    Accepts JSON payload:
    {
      "deficit": {"Carbohydrates_g":.., "Protein_g":.., ...}, 
      "candidate_ids": [optional list of food ids],
      "top_k": 5
    }
    Returns list of recommendations
    """
    # payload may come as str
    if isinstance(json_payload, str):
        payload = json.loads(json_payload)
    else:
        payload = json_payload
    deficit = payload.get("deficit", {})
    top_k = int(payload.get("top_k", 8))
    # if candidate_ids provided, filter foods_df
    cand = df_foods
    if "candidate_ids" in payload and payload["candidate_ids"]:
        cand = df_foods[df_foods.food_id.isin(payload["candidate_ids"])]
    recs = score_candidates(deficit, cand, top_k=top_k)
    return recs

# Minimal Gradio UI + API
with gr.Blocks() as demo:
    gr.Markdown("# NutriMate Recommender (demo)")
    with gr.Row():
        deficit_text = gr.Textbox(label="JSON payload (deficit + optional candidate_ids)", value='{\"deficit\": {\"Protein_g\": 50, \"Carbohydrates_g\": 100}}', lines=4)
        btn = gr.Button("Recommend")
    out = gr.JSON()
    btn.click(fn=recommend_api, inputs=deficit_text, outputs=out)

demo.launch(server_name="0.0.0.0", server_port=7860)