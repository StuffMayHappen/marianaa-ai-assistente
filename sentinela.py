import os
import json
import queue
import subprocess
import sounddevice as sd
from vosk import Model, KaldiRecognizer, SetLogLevel

# Silenciar os logs irritantes do Vosk no terminal
SetLogLevel(-1)

# Configuração minimalista e leve
VOSK_MODEL_PT = "modelos_voz/vosk-model-small-pt-0.3"
audio_queue = queue.Queue()

def callback(indata, frames, time, status):
    audio_queue.put(bytes(indata))

def marianaa_ja_acordou():
    """Verifica os processos do Linux para garantir que não explodimos a RTX 3050 abrindo a IA duas vezes."""
    try:
        output = subprocess.check_output(["pgrep", "-f", "app.py"]).decode("utf-8")
        return len(output.strip()) > 0
    except subprocess.CalledProcessError:
        return False

def vigiar():
    print("\n" + "🛡️ "*15)
    print("[ SENTINELA ATIVADO ] - Modo de Baixo Consumo")
    print("A gráfica está a dormir. O Sentinela está à escuta pelo microfone...")
    print("Grita 'Mariana acorda' ou 'Acorda Mariana' para iniciar o sistema.")
    print("🛡️ "*15 + "\n")

    try:
        model = Model(VOSK_MODEL_PT)
        rec = KaldiRecognizer(model, 16000)
    except Exception as e:
        print(f"[!] Erro Fatal no Ouvido do Sentinela: {e}")
        return

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=callback):
        while True:
            data = audio_queue.get()
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                texto = res.get("text", "").lower()

                # --- ADICIONA ESTA LINHA AQUI ---
                if texto:
                    print(f"[DEBUG OUVINDO]: '{texto}'")
                # --------------------------------

                # O Gatilho à Prova de Bala (Ignora erros de fonética)
                if "mariana" in texto and ("acorda" in texto or "a corda" in texto or "corda" in texto or "inicia" in texto):
                    print(f"\n[!] Comando de voz detetado: '{texto}'")
                    
                    if marianaa_ja_acordou():
                        print("[⚠️] O Sentinela bloqueou a ação: A Marianaa já está a correr no sistema!")
                        print("[⚠️] Não vou abrir duas vezes para não te queimar a placa gráfica.")
                    else:
                        print("[⚡] Acesso concedido. A injetar o Cérebro 8B na VRAM...")
                        print("[🚀] Podes ir para a interface gráfica. O Sentinela vai continuar a vigiar nas sombras.\n")
                        
                        # Inicia o app.py de forma limpa e independente sem bloquear o sentinela
                        subprocess.Popen(["python", "app.py"])

if __name__ == "__main__":
    vigiar()
