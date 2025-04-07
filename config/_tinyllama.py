import torch

TINYLLAMA_MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
TINYLLAMA_DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'