import os
import json
from fastapi import FastAPI, Request
import google.generativeai as genai
from pydantic import BaseModel
from typing import List

app = FastAPI()

# កំណត់ការភ្ជាប់ជាមួយ Gemini API
# កុំភ្លេចដាក់ GEMINI_API_KEY ក្នុង Environment Variables របស់ Railway
genai.configure(api_key=os.environ.get("AIzaSyDZ0LxeLj2laZmA9AZo6L9yqzzthZKyRno"))
model = genai.GenerativeModel('gemini-1.5-flash')

class Candle(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: int

class AnalysisRequest(BaseModel):
    symbol: str
    timeframe: str
    position_status: str  # "NONE", "BUY", ឬ "SELL"
    candles: List[Candle]

@app.get("/")
def read_root():
    return {"status": "AI Trading Server is running"}

@app.post("/analyze")
async def analyze_market(data: AnalysisRequest):
    # រៀបចំទិន្នន័យ Candle ជាអត្ថបទសម្រាប់ឱ្យ AI មើល
    candle_str = ""
    for c in data.candles:
        candle_str += f"T: {c.time}, O: {c.open}, H: {c.high}, L: {c.low}, C: {c.close}\n"

    # បង្កើត Prompt ឱ្យមានលក្ខណៈជា Expert Trader
    prompt = f"""
    You are a professional algorithmic trader. Analyze the following {data.timeframe} data for {data.symbol}:
    
    Current Position: {data.position_status}
    
    Recent Price Data:
    {candle_str}
    
    Task:
    1. If position_status is 'NONE', decide if we should ENTER (BUY, SELL, or WAIT).
    2. If position_status is 'BUY' or 'SELL', decide if we should HOLD or CLOSE.
    3. Minimum confidence for entry is 70%.
    
    Response must be strictly in JSON format like this:
    {{
        "decision": "BUY/SELL/WAIT/HOLD/CLOSE",
        "confidence": 0-100,
        "analysis": "short technical reason"
    }}
    """

    try:
        response = model.generate_content(prompt)
        # សម្អាតអត្ថបទដែល AI ផ្ដល់មក (ជួនកាល AI ថែម ```json ... ```)
        clean_response = response.text.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_response)
        return result
    except Exception as e:
        return {"decision": "WAIT", "confidence": 0, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
