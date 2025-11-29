"""
Chart Renderer Module
Responsible for converting raw MT5 price data into machine-readable candlestick charts.
"""

import pandas as pd
import mplfinance as mpf
import io
import base64
from loguru import logger
from datetime import datetime
import os

class ChartRenderer:
    """
    Renders financial charts for Vision Agent analysis.
    """
    
    def __init__(self, style: str = 'nightclouds', dpi: int = 100):
        self.style = style
        self.dpi = dpi
        self.output_dir = "data/charts"
        os.makedirs(self.output_dir, exist_ok=True)

    def process_data(self, rates) -> pd.DataFrame:
        """
        Convert MT5 rates (numpy array of tuples) to Pandas DataFrame.
        Expected columns: time, open, high, low, close, tick_volume, spread, real_volume
        """
        try:
            df = pd.DataFrame(rates)
            # Convert time (seconds) to datetime
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Rename columns to match mplfinance expectations
            df.rename(columns={
                'open': 'Open', 
                'high': 'High', 
                'low': 'Low', 
                'close': 'Close', 
                'tick_volume': 'Volume'
            }, inplace=True)
            
            return df
        except Exception as e:
            logger.error(f"Failed to process data: {e}")
            return pd.DataFrame()

    def render_chart(self, symbol: str, rates, filename: str = None) -> str:
        """
        Render a chart and return the path to the image file.
        """
        df = self.process_data(rates)
        if df.empty:
            logger.warning(f"No data to render for {symbol}")
            return None
            
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{symbol}_{timestamp}.png"
            
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # Create custom style based on 'nightclouds' but with specific tweaks if needed
            # For now, standard nightclouds is excellent for high contrast
            
            mpf.plot(
                df,
                type='candle',
                style=self.style,
                volume=True,
                mav=(20, 50), # Moving averages for trend context
                title=f"{symbol} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                savefig=dict(fname=filepath, dpi=self.dpi, pad_inches=0.25),
                block=False
            )
            
            logger.info(f"Chart rendered: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to render chart for {symbol}: {e}")
            return None

    def get_base64_image(self, filepath: str) -> str:
        """
        Convert image file to Base64 string for API transmission.
        """
        try:
            with open(filepath, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encode image {filepath}: {e}")
            return None

# Test execution
if __name__ == "__main__":
    # Mock data for testing
    import numpy as np
    
    print("Testing ChartRenderer...")
    
    # Create dummy data resembling MT5 output
    # time, open, high, low, close, tick_volume, spread, real_volume
    now = int(datetime.now().timestamp())
    data = []
    price = 1.1000
    for i in range(100):
        time = now - (100 - i) * 60
        open_p = price
        close_p = price + np.random.uniform(-0.0005, 0.0005)
        high_p = max(open_p, close_p) + np.random.uniform(0, 0.0002)
        low_p = min(open_p, close_p) - np.random.uniform(0, 0.0002)
        vol = int(np.random.uniform(10, 100))
        data.append((time, open_p, high_p, low_p, close_p, vol, 0, 0))
        price = close_p
        
    # Convert to numpy structured array (simulating MT5)
    dtype = [('time', '<i8'), ('open', '<f8'), ('high', '<f8'), ('low', '<f8'), ('close', '<f8'), ('tick_volume', '<i8'), ('spread', '<i8'), ('real_volume', '<i8')]
    rates = np.array(data, dtype=dtype)
    
    renderer = ChartRenderer()
    path = renderer.render_chart("TEST_EURUSD", rates)
    
    if path:
        print(f"✅ Success! Chart saved to: {path}")
    else:
        print("❌ Failed to render chart.")
