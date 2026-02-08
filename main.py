import os
import json
from fastapi import FastAPI
import google.generativeai as genai
from pydantic import BaseModel
from typing import List

app = FastAPI()

# កំណត់ API Key (យកពី Google AI Studio)
genai.configure(api_key=os.environ.get("AIzaSyDZ0LxeLj2laZmA9AZo6L9yqzzthZKyRno"))
model = genai.GenerativeModel('gemini-1.5-flash')

class Candle(BaseModel):
    t: str # time
    o: float # open
    h: float # high
    l: float # low
    c: float # close

class AnalysisRequest(BaseModel):
    symbol: str
    pos_status: str
    candles: List[Candle]

@app.post("/analyze")
async def analyze_market(data: AnalysisRequest):
    price_data = "\n".join([f"{c.t}: O:{c.o} H:{c.h} L:{c.l} C:{c.c}" for c in data.candles])
    
    prompt = f"""
    You are a Senior Forex Trader. Analyze {data.symbol} M1 data:
    {price_data}

    Current Status: {data.pos_status}

    Task:
    1. If status is 'NONE', decide: BUY, SELL, or WAIT.
    2. If status is 'OPEN', decide: HOLD or CLOSE.
    3. Provide precise SL and TP prices based on technical levels (Support/Resistance).

    Response must be strictly JSON:
    {{
        "decision": "BUY/SELL/WAIT/HOLD/CLOSE",
        "confidence": 0-100,
        "sl": price,
        "tp": price,
        "reason": "short text"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        # សម្អាត JSON string
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except:
        return {"decision": "WAIT", "confidence": 0, "sl": 0, "tp": 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
