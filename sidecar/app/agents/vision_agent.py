"""
Vision Agent Module
Uses Multimodal LLMs to analyze financial charts.
"""

import os
import json
import base64
from loguru import logger
from openai import OpenAI
from app.core.config import settings
from app.data.chart_renderer import ChartRenderer
from app.data.mt5_client import mt5_client
import MetaTrader5 as mt5

class VisionAgent:
    """
    The 'Eyes' of the system. Analyzes charts for patterns and sentiment.
    """
    
    def __init__(self):
        self.renderer = ChartRenderer()
        # Initialize OpenAI client with OpenRouter base URL
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )
        # Model: Nvidia Nemotron Nano 12B VL (Free Tier)
        self.model = "nvidia/nemotron-nano-12b-v2-vl:free"
        logger.info(f"VisionAgent initialized with model: {self.model}")

    def analyze(self, symbol: str, timeframe=None) -> dict:
        """
        Capture chart and analyze it using VLM.
        """
        logger.info(f"VisionAgent analyzing {symbol}...")
        
        # 1. Fetch Data (Real MT5 Data)
        # Default to M15 timeframe (15 minutes)
        tf = timeframe if timeframe else mt5.TIMEFRAME_M15
        
        rates = mt5_client.get_rates(symbol, tf, count=100)
        if rates is None:
            logger.warning(f"Could not fetch rates for {symbol}")
            return {"error": "No data"}

        # 2. Render Chart
        image_path = self.renderer.render_chart(symbol, rates)
        if not image_path:
            return {"error": "Rendering failed"}

        # 3. Encode Image
        base64_image = self.renderer.get_base64_image(image_path)
        if not base64_image:
            return {"error": "Encoding failed"}

        # 4. Ask the AI
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional Prop Trader. Analyze the chart image. Output ONLY valid JSON with keys: 'market_structure' (Bullish/Bearish/Ranging), 'patterns' (list of strings), 'key_levels' (list of prices), 'sentiment_score' (-1.0 to 1.0)."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"Analyze this M15 chart for {symbol}."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.1, # Low temperature for factual analysis
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            logger.info(f"Vision Analysis: {content}")
            
            # Parse JSON from response (handle potential markdown fences)
            clean_content = content.replace("", "").strip()
            # Find the first { and last } to extract JSON if there's extra text
            start = clean_content.find("{")
            end = clean_content.rfind("}") + 1
            if start != -1 and end != -1:
                clean_content = clean_content[start:end]
                
            return json.loads(clean_content)

        except Exception as e:
            logger.error(f"Vision API failed: {e}")
            return {"error": str(e)}

# Test execution
if __name__ == "__main__":
    # Simple test wrapper
    agent = VisionAgent()
    
    print("Testing VisionAgent...")
    if not settings.openrouter_api_key:
        print("❌ OPENROUTER_API_KEY not set in .env or config!")
    else:
        # Try to analyze a symbol (assuming MT5 is running)
        # We need to make sure MT5 is connected for this test to work fully
        if mt5_client.connect():
            result = agent.analyze("EURUSD")
            print(f"Result: {json.dumps(result, indent=2)}")
        else:
            print("❌ MT5 not connected. Cannot fetch real data for test.")
