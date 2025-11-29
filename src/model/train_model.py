"""
Training script for binary cry vs no-cry classification model.
Processes 7-second audio windows from .wav and .ogg files.
"""

import os
import glob
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
import torchaudio
import numpy as np
from pathlib import Path
from tqdm import tqdm
import argparse

# Try to import librosa for .ogg file support
try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

# Configuration
SAMPLE_RATE = 16000
WINDOW_DURATION = 7  # seconds
WINDOW_SAMPLES = SAMPLE_RATE * WINDOW_DURATION  # 112000 samples
BATCH_SIZE = 32
LEARNING_RATE = 0.001
NUM_EPOCHS = 50
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class CryDataset(Dataset):
    """Dataset for loading cry and no-cry audio files."""
    
    def __init__(self, data_dir, transform=None):
        """
        Args:
            data_dir: Path to the data directory containing 'cry' and 'not_cry' folders
            transform: Optional transform to apply to audio
        """
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.samples = []
        
        # Load cry samples (label = 1)
        cry_dir = self.data_dir / "cry"
        if cry_dir.exists():
            for ext in ["*.wav", "*.ogg"]:
                for file_path in glob.glob(str(cry_dir / ext)):
                    self.samples.append((file_path, 1))
        
        # Load not_cry samples (label = 0)
        not_cry_dir = self.data_dir / "not_cry"
        if not_cry_dir.exists():
            for ext in ["*.wav", "*.ogg"]:
                for file_path in glob.glob(str(not_cry_dir / ext)):
                    self.samples.append((file_path, 0))
        
        print(f"Loaded {len([s for s in self.samples if s[1] == 1])} cry samples")
        print(f"Loaded {len([s for s in self.samples if s[1] == 0])} no-cry samples")
        print(f"Total samples: {len(self.samples)}")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        file_path, label = self.samples[idx]
        
        try:
            # Load audio file - use librosa if available (handles both .wav and .ogg reliably)
            # Otherwise try torchaudio with librosa as fallback
            if HAS_LIBROSA:
                # Use librosa for all files (handles .wav, .ogg, and other formats reliably)
                waveform_np, sr = librosa.load(file_path, sr=SAMPLE_RATE, mono=True)
                waveform = torch.from_numpy(waveform_np).float()
                # librosa already returns mono and resampled to SAMPLE_RATE
            else:
                # Fallback to torchaudio if librosa is not available
                try:
                    waveform, sr = torchaudio.load(file_path)
                    
                    # Resample if necessary
                    if sr != SAMPLE_RATE:
                        resampler = torchaudio.transforms.Resample(sr, SAMPLE_RATE)
                        waveform = resampler(waveform)
                    
                    # Convert to mono if stereo (torchaudio returns [channels, samples])
                    if waveform.dim() > 1 and waveform.shape[0] > 1:
                        waveform = torch.mean(waveform, dim=0, keepdim=True)
                    
                    # Ensure we have the right shape: [samples] (1D tensor)
                    if waveform.dim() > 1:
                        waveform = waveform.squeeze(0)
                except Exception as e:
                    raise RuntimeError(f"Failed to load {file_path} with torchaudio. Install librosa for better format support: {e}")
            
            # Ensure waveform is 1D (librosa already returns 1D, torchaudio we handled above)
            if waveform.dim() > 1:
                waveform = waveform.squeeze(0)
            
            # Pad or truncate to exactly WINDOW_SAMPLES
            if len(waveform) < WINDOW_SAMPLES:
                # Pad with zeros
                padding = WINDOW_SAMPLES - len(waveform)
                waveform = torch.nn.functional.pad(waveform, (0, padding))
            elif len(waveform) > WINDOW_SAMPLES:
                # Truncate to first WINDOW_SAMPLES
                waveform = waveform[:WINDOW_SAMPLES]
            
            # Normalize to [-1, 1] range
            if waveform.abs().max() > 0:
                waveform = waveform / waveform.abs().max()
            
            # Apply transform if provided
            if self.transform:
                waveform = self.transform(waveform)
            
            return waveform.unsqueeze(0), torch.tensor(label, dtype=torch.long)
        
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            # Return a zero tensor as fallback
            return torch.zeros(1, WINDOW_SAMPLES), torch.tensor(label, dtype=torch.long)


class CryClassifier(nn.Module):
    """CNN-based model for binary cry classification."""
    
    def __init__(self):
        super(CryClassifier, self).__init__()
        
        # First conv block
        self.conv1 = nn.Sequential(
            nn.Conv1d(1, 32, kernel_size=7, stride=2, padding=3),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(2)
        )
        
        # Second conv block
        self.conv2 = nn.Sequential(
            nn.Conv1d(32, 64, kernel_size=5, stride=2, padding=2),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2)
        )
        
        # Third conv block
        self.conv3 = nn.Sequential(
            nn.Conv1d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.MaxPool1d(2)
        )
        
        # Fourth conv block
        self.conv4 = nn.Sequential(
            nn.Conv1d(128, 256, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.MaxPool1d(2)
        )
        
        # Global average pooling
        self.global_pool = nn.AdaptiveAvgPool1d(1)
        
        # Classifier
        self.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, 2)  # Binary classification
        )
    
    def forward(self, x):
        # x shape: [batch, 1, WINDOW_SAMPLES]
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.global_pool(x)  # [batch, 256, 1]
        x = x.squeeze(-1)  # [batch, 256]
        x = self.classifier(x)
        return x


def train_epoch(model, dataloader, criterion, optimizer, device):
    """Train for one epoch."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for waveforms, labels in tqdm(dataloader, desc="Training"):
        waveforms = waveforms.to(device)
        labels = labels.to(device)
        
        # Forward pass
        optimizer.zero_grad()
        outputs = model(waveforms)
        loss = criterion(outputs, labels)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        # Statistics
        running_loss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
    
    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100 * correct / total
    return epoch_loss, epoch_acc


def validate(model, dataloader, criterion, device):
    """Validate the model."""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for waveforms, labels in tqdm(dataloader, desc="Validating"):
            waveforms = waveforms.to(device)
            labels = labels.to(device)
            
            outputs = model(waveforms)
            loss = criterion(outputs, labels)
            
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    
    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100 * correct / total
    return epoch_loss, epoch_acc


def main():
    parser = argparse.ArgumentParser(description="Train cry detection model")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="src/model/data",
        help="Path to data directory containing cry/ and not_cry/ folders"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Batch size (default: {BATCH_SIZE})"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=NUM_EPOCHS,
        help=f"Number of epochs (default: {NUM_EPOCHS})"
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=LEARNING_RATE,
        help=f"Learning rate (default: {LEARNING_RATE})"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="src/model/checkpoints",
        help="Directory to save model checkpoints"
    )
    parser.add_argument(
        "--val-split",
        type=float,
        default=0.2,
        help="Validation split ratio (default: 0.2)"
    )
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Using device: {DEVICE}")
    print(f"Window duration: {WINDOW_DURATION}s ({WINDOW_SAMPLES} samples)")
    print(f"Sample rate: {SAMPLE_RATE} Hz")
    
    # Load dataset
    print("\nLoading dataset...")
    dataset = CryDataset(args.data_dir)
    
    if len(dataset) == 0:
        print("Error: No samples found in dataset!")
        return
    
    # Split into train and validation
    val_size = int(len(dataset) * args.val_split)
    train_size = len(dataset) - val_size
    train_dataset, val_dataset = random_split(
        dataset, [train_size, val_size],
        generator=torch.Generator().manual_seed(42)
    )
    
    print(f"Train samples: {len(train_dataset)}")
    print(f"Validation samples: {len(val_dataset)}")
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=4,
        pin_memory=True if torch.cuda.is_available() else False
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=4,
        pin_memory=True if torch.cuda.is_available() else False
    )
    
    # Initialize model
    print("\nInitializing model...")
    model = CryClassifier().to(DEVICE)
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5
    )
    
    # Training loop
    print("\nStarting training...")
    best_val_acc = 0.0
    
    for epoch in range(args.epochs):
        print(f"\nEpoch {epoch+1}/{args.epochs}")
        print("-" * 50)
        
        # Train
        train_loss, train_acc = train_epoch(
            model, train_loader, criterion, optimizer, DEVICE
        )
        
        # Validate
        val_loss, val_acc = validate(model, val_loader, criterion, DEVICE)
        
        # Learning rate scheduling
        scheduler.step(val_loss)
        
        print(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
        print(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            checkpoint_path = os.path.join(args.output_dir, "best_model.pt")
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc,
                'val_loss': val_loss,
            }, checkpoint_path)
            print(f"Saved best model (val_acc: {val_acc:.2f}%)")
        
        # Save checkpoint every 10 epochs
        if (epoch + 1) % 10 == 0:
            checkpoint_path = os.path.join(args.output_dir, f"checkpoint_epoch_{epoch+1}.pt")
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc,
                'val_loss': val_loss,
            }, checkpoint_path)
    
    print("\nTraining completed!")
    print(f"Best validation accuracy: {best_val_acc:.2f}%")


if __name__ == "__main__":
    main()

