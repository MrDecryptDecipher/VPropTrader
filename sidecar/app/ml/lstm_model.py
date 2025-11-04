"""2-Head LSTM for Volatility and Direction Forecasting"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
from typing import Tuple, Dict, Optional
from loguru import logger
from app.core import settings


class LSTMDataset(Dataset):
    """Dataset for LSTM training"""
    
    def __init__(self, sequences: np.ndarray, targets: np.ndarray):
        self.sequences = torch.FloatTensor(sequences)
        self.targets = torch.FloatTensor(targets)
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.targets[idx]


class TwoHeadLSTM(nn.Module):
    """2-Head LSTM: one head for volatility, one for direction"""
    
    def __init__(self, input_size: int = 50, hidden_size: int = 64, num_layers: int = 2):
        super(TwoHeadLSTM, self).__init__()
        
        # Shared LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2 if num_layers > 1 else 0
        )
        
        # Volatility head (regression)
        self.vol_head = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),
            nn.Softplus()  # Ensure positive output
        )
        
        # Direction head (regression, -1 to +1)
        self.dir_head = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),
            nn.Tanh()  # Output between -1 and +1
        )
    
    def forward(self, x):
        # x shape: (batch, sequence_length, features)
        lstm_out, _ = self.lstm(x)
        
        # Use last time step
        last_hidden = lstm_out[:, -1, :]
        
        # Two heads
        volatility = self.vol_head(last_hidden)
        direction = self.dir_head(last_hidden)
        
        return volatility, direction


class LSTMModel:
    """LSTM model manager"""
    
    def __init__(self):
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_path = Path(settings.model_path) / "lstm_2head.pt"
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"LSTM using device: {self.device}")
    
    def train(
        self,
        sequences: np.ndarray,
        targets: np.ndarray,
        epochs: int = 50,
        batch_size: int = 32,
        learning_rate: float = 0.001,
        val_split: float = 0.2
    ) -> Dict[str, float]:
        """
        Train LSTM model
        
        Args:
            sequences: Input sequences (n_samples, sequence_length, features)
            targets: Target values (n_samples, 2) - [volatility, direction]
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
            val_split: Validation split ratio
        
        Returns:
            Dict with training metrics
        """
        try:
            logger.info(f"Training LSTM on {len(sequences)} sequences...")
            
            # Split data
            n_val = int(len(sequences) * val_split)
            n_train = len(sequences) - n_val
            
            train_sequences = sequences[:n_train]
            train_targets = targets[:n_train]
            val_sequences = sequences[n_train:]
            val_targets = targets[n_train:]
            
            # Create datasets
            train_dataset = LSTMDataset(train_sequences, train_targets)
            val_dataset = LSTMDataset(val_sequences, val_targets)
            
            train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
            
            # Create model
            input_size = sequences.shape[2]
            self.model = TwoHeadLSTM(input_size=input_size).to(self.device)
            
            # Loss and optimizer
            criterion = nn.MSELoss()
            optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
            
            # Training loop
            best_val_loss = float('inf')
            patience_counter = 0
            max_patience = 10
            
            for epoch in range(epochs):
                # Train
                self.model.train()
                train_loss = 0.0
                
                for batch_seq, batch_target in train_loader:
                    batch_seq = batch_seq.to(self.device)
                    batch_target = batch_target.to(self.device)
                    
                    optimizer.zero_grad()
                    
                    vol_pred, dir_pred = self.model(batch_seq)
                    
                    # Separate losses
                    vol_loss = criterion(vol_pred.squeeze(), batch_target[:, 0])
                    dir_loss = criterion(dir_pred.squeeze(), batch_target[:, 1])
                    
                    # Combined loss
                    loss = vol_loss + dir_loss
                    
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                    optimizer.step()
                    
                    train_loss += loss.item()
                
                train_loss /= len(train_loader)
                
                # Validate
                self.model.eval()
                val_loss = 0.0
                
                with torch.no_grad():
                    for batch_seq, batch_target in val_loader:
                        batch_seq = batch_seq.to(self.device)
                        batch_target = batch_target.to(self.device)
                        
                        vol_pred, dir_pred = self.model(batch_seq)
                        
                        vol_loss = criterion(vol_pred.squeeze(), batch_target[:, 0])
                        dir_loss = criterion(dir_pred.squeeze(), batch_target[:, 1])
                        
                        loss = vol_loss + dir_loss
                        val_loss += loss.item()
                
                val_loss /= len(val_loader)
                
                # Learning rate scheduling
                scheduler.step(val_loss)
                
                # Early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")
                
                if patience_counter >= max_patience:
                    logger.info(f"Early stopping at epoch {epoch+1}")
                    break
            
            metrics = {
                "train_loss": float(train_loss),
                "val_loss": float(val_loss),
                "best_val_loss": float(best_val_loss),
                "epochs_trained": epoch + 1,
                "train_samples": n_train,
                "val_samples": n_val,
            }
            
            logger.info(f"✓ LSTM trained - Best Val Loss: {best_val_loss:.6f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error training LSTM: {e}", exc_info=True)
            return {}
    
    def predict(self, sequence: np.ndarray) -> Tuple[float, float]:
        """
        Predict volatility and direction
        
        Args:
            sequence: Input sequence (sequence_length, features)
        
        Returns:
            (volatility_forecast, direction_forecast)
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        self.model.eval()
        
        with torch.no_grad():
            # Add batch dimension
            seq_tensor = torch.FloatTensor(sequence).unsqueeze(0).to(self.device)
            
            vol_pred, dir_pred = self.model(seq_tensor)
            
            volatility = vol_pred.item()
            direction = dir_pred.item()
        
        return volatility, direction
    
    def save(self) -> bool:
        """Save model to disk"""
        if self.model is None:
            logger.warning("No model to save")
            return False
        
        try:
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'model_config': {
                    'input_size': self.model.lstm.input_size,
                    'hidden_size': self.model.lstm.hidden_size,
                    'num_layers': self.model.lstm.num_layers,
                }
            }, self.model_path)
            
            logger.info(f"✓ LSTM saved to {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving LSTM: {e}")
            return False
    
    def load(self) -> bool:
        """Load model from disk"""
        if not self.model_path.exists():
            logger.warning(f"Model file not found: {self.model_path}")
            return False
        
        try:
            checkpoint = torch.load(self.model_path, map_location=self.device)
            
            config = checkpoint['model_config']
            self.model = TwoHeadLSTM(
                input_size=config['input_size'],
                hidden_size=config['hidden_size'],
                num_layers=config['num_layers']
            ).to(self.device)
            
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.eval()
            
            logger.info(f"✓ LSTM loaded from {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading LSTM: {e}")
            return False


# Global LSTM instance
lstm_model = LSTMModel()
