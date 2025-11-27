"""
Transformer Model for Time Series Forecasting
Implements a simplified Temporal Fusion Transformer (TFT) architecture.
"""

import torch
import torch.nn as nn
import math
import logging

logger = logging.getLogger(__name__)

class TimeSeriesTransformer(nn.Module):
    """
    Transformer-based model for price prediction.
    """
    def __init__(self, input_dim=10, d_model=64, nhead=4, num_layers=2, output_dim=1, dropout=0.1):
        super(TimeSeriesTransformer, self).__init__()
        
        self.input_embedding = nn.Linear(input_dim, d_model)
        self.pos_encoder = PositionalEncoding(d_model, dropout)
        
        encoder_layers = nn.TransformerEncoderLayer(d_model, nhead, dim_feedforward=d_model*4, dropout=dropout, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers)
        
        self.decoder = nn.Linear(d_model, output_dim)
        self.sigmoid = nn.Sigmoid()

    def forward(self, src):
        """
        src: [batch_size, seq_len, input_dim]
        """
        # Embed
        src = self.input_embedding(src) # [batch, seq, d_model]
        src = self.pos_encoder(src)
        
        # Transform
        output = self.transformer_encoder(src) # [batch, seq, d_model]
        
        # Decode (use last time step for prediction)
        last_step = output[:, -1, :] # [batch, d_model]
        prediction = self.decoder(last_step) # [batch, output_dim]
        
        return self.sigmoid(prediction) # Probability of Up/Down or normalized price

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:, :x.size(1)]
        return self.dropout(x)

# Global Inference Helper
class TransformerPredictor:
    def __init__(self, model_path=None):
        self.model = TimeSeriesTransformer()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        
        if model_path:
            try:
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
                logger.info(f"Loaded Transformer model from {model_path}")
            except Exception as e:
                logger.warning(f"Could not load model: {e}")

    def predict(self, features_sequence):
        """
        features_sequence: List of feature vectors (seq_len, input_dim)
        """
        try:
            tensor = torch.FloatTensor(features_sequence).unsqueeze(0).to(self.device) # [1, seq, dim]
            with torch.no_grad():
                pred = self.model(tensor)
            return pred.item()
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return 0.5

# Global instance
transformer_predictor = TransformerPredictor()
