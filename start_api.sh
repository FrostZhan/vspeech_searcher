#!/bin/bash



llama-server -m models\nomic-embed-text-v2-moe.f16.gguf --embeddings
.venv/Scripts/Activate.ps1
python api.py
