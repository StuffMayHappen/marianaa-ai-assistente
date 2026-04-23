#!/bin/bash

echo "[🧹] Marianaa > A incinerar a compilação antiga..."
rm -rf build dist Marianaa_AI.spec

echo "[🎨] Marianaa > A preparar o novo rosto com o logo..."

pyinstaller --noconsole \
    --name "Marianaa_AI_Assistente" \
    --icon="/home/walterlandd/Pictures/logo_app_ai.png" \
    --add-data "web:web" \
    app.py

echo "[⚙️] Marianaa > A repor os cérebros na pasta de distribuição..."
cp -r models dist/Marianaa_AI_Assistente/
cp -r modelos_voz dist/Marianaa_AI_Assistente/
cp config.json dist/Marianaa_AI_Assistente/

echo "[✅] Marianaa > Compilação terminada! A verificar integridade..."
if [ -f "dist/Marianaa_AI_Assistente/Marianaa_AI_Assistente" ]; then
    echo "[🚀] Sistema operacional. Podes encontrar-me em: dist/Marianaa_AI_Assistente/"
else
    echo "[💀] Erro crítico na forja. Revisa os logs."
fi
