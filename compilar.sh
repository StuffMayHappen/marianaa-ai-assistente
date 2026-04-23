#!/bin/bash
echo "[🧹] Marianaa > A incinerar a compilação antiga..."
rm -rf build dist Marianaa_AI_Assistente.spec

echo "[🎨] Marianaa > A forjar a app (com ouvidos Vosk blindados)..."
# A MÁGICA ESTÁ AQUI: --collect-all vosk
pyinstaller --noconsole \
    --name "Marianaa_AI_Assistente" \
    --add-data "web:web" \
    --collect-all vosk \
    --collect-all llama_cpp \
    app.py

echo "[⚙️] Marianaa > A repor os cérebros na pasta de distribuição..."
cp -r models dist/Marianaa_AI_Assistente/
cp -r modelos_voz dist/Marianaa_AI_Assistente/
cp -r docs dist/Marianaa_AI_Assistente/
cp config.json dist/Marianaa_AI_Assistente/
cp /home/walterlandd/Pictures/logo_app_ai.png dist/Marianaa_AI_Assistente/

echo "[✅] Marianaa > Compilação e preparação terminadas!"
