#!/bin/bash

echo "[🚀] A iniciar a instalação da Marianaa AI..."

USER_DIR="$HOME/.local/share/MarianaaAI"
DESKTOP_FILE="$HOME/.local/share/applications/marianaa.desktop"
ICON_DIR="$HOME/.local/share/icons"

mkdir -p "$USER_DIR"
mkdir -p "$ICON_DIR"

echo "[📦] A copiar os ficheiros do núcleo..."
cp -r ./* "$USER_DIR/"

cp "$USER_DIR/logo_app_ai.png" "$ICON_DIR/marianaa_logo.png"

echo "[🔗] A criar integração com o Menu e a Barra de Tarefas..."
cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Name=Marianaa AI
Comment=Assistente Pessoal Inteligente
Exec=$USER_DIR/Marianaa_AI_Assistente
Icon=marianaa_logo
Terminal=false
Type=Application
Categories=Utility;
EOF

chmod +x "$DESKTOP_FILE"

echo "=========================================="
echo "[✅] INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
echo "=========================================="
echo "A Marianaa já está no teu Menu de Aplicações."
echo "Podes procurá-la pelo nome e fixá-la na tua Barra de Tarefas."
sleep 3

