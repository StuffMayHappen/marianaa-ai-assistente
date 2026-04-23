import os, json, queue, threading, wave, subprocess, time, io, urllib.request, asyncio, sys
from datetime import datetime
import eel, sounddevice as sd, numpy as np, edge_tts, speech_recognition as sr
from vosk import Model, KaldiRecognizer, SetLogLevel
from langchain_community.llms import LlamaCpp
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI # <--- O CONECTOR DA CLOUD

# ==========================================
# GESTÃO DE CAMINHOS DINÂMICOS E INTERNET
# ==========================================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_path(rel_path):
    return os.path.join(BASE_DIR, rel_path)

def tem_internet():
    try:
        urllib.request.urlopen('http://clients3.google.com/generate_204', timeout=2)
        return True
    except: return False

for folder in ["memories", "docs", "modelos_voz", "models"]:
    os.makedirs(get_path(folder), exist_ok=True)

CONFIG_FILE = get_path("config.json")
os.environ["HF_HUB_OFFLINE"] = "1"
SetLogLevel(-1)

eel.init(get_path('web'))

def load_config():
    if not os.path.exists(CONFIG_FILE):
        # AQUI FOI ADICIONADA A API KEY
        default = {"ai_name": "Marianaa", "wake_word": "mariana", "theme": "dark", "accent_color": "#9b59b6", "language": "pt", "api_key": ""}
        with open(CONFIG_FILE, "w") as f: json.dump(default, f, indent=4)
    with open(CONFIG_FILE, "r") as f: return json.load(f)

@eel.expose
def get_config(): return load_config()

@eel.expose
def save_config(new_cfg):
    # Mantém a api_key existente caso a interface web não a envie
    cfg_atual = load_config()
    if 'api_key' in cfg_atual: new_cfg['api_key'] = cfg_atual['api_key']
    with open(CONFIG_FILE, "w") as f: json.dump(new_cfg, f, indent=4)

# --- CORDAS VOCAIS ---
def falar_texto(texto, bloqueante=False):
    cfg = load_config()
    async def amain():
        voice = "pt-PT-RaquelNeural" if cfg['language'] == "pt" else "en-US-AvaNeural"
        communicate = edge_tts.Communicate(texto, voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": audio_data += chunk["data"]
        
        if audio_data:
            process = subprocess.Popen(
                ['ffmpeg', '-i', 'pipe:0', '-f', 'f32le', '-acodec', 'pcm_f32le', '-ar', '44100', 'pipe:1'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            )
            out, _ = process.communicate(input=audio_data)
            som = np.frombuffer(out, dtype=np.float32).reshape(-1, 1)
            sd.play(som, 44100)
            sd.wait()

    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop); loop.run_until_complete(amain())
    
    if bloqueante: run()
    else: threading.Thread(target=run, daemon=True).start()

# --- MONSTRO 8B OU CLOUD-ONLY ---
cfg_inicial = load_config()
modo_cloud = cfg_inicial.get("cloud_only", False)

if not modo_cloud:
    print("[🔥] Marianaa > A injetar Monstro 8B na RAM...")
    try:
        llm = LlamaCpp(
            model_path=get_path("models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"), 
            n_ctx=32768, n_gpu_layers=10, n_threads=12, use_mlock=True, offload_kqv=False, verbose=False
        )
    except Exception as e:
        print(f"[❌] Erro ao carregar modelo local: {e}")
        llm = None
else:
    print("[☁️] Marianaa > MODO CLOUD-ONLY ATIVADO. Monstro local adormecido (RAM poupada).")
    llm = None

@eel.expose
def processar_pergunta(pergunta, usou_voz=False):
    cfg = load_config()
    api_key = cfg.get("api_key", "").strip()
    modo_cloud_ativo = cfg.get("cloud_only", False)
    
    if pergunta.strip().lower() in ["ou a", "alla", "olha", "a"]: pergunta = "olá"
    
    template = f"<|start_header_id|>system<|end_header_id|>\nÉs a {cfg['ai_name']}. Responde de forma curta e sarcástica.<|eot_id|><|start_header_id|>user<|end_header_id|>{{question}}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
    prompt = PromptTemplate(template=template, input_variables=["question"])
    
    resposta = ""
    
    if api_key and tem_internet():
        try:
            print("[☁️] A processar na Cloud...")
            cloud_llm = ChatOpenAI(
                openai_api_base="https://openrouter.ai/api/v1", openai_api_key=api_key,
                model_name="meta-llama/llama-3-8b-instruct:free", max_tokens=250, temperature=0.8
            )
            resposta = cloud_llm.invoke(prompt.format(question=pergunta)).content.strip()
        except Exception as e:
            print(f"[⚠️] Cloud falhou: {e}")
            if not modo_cloud_ativo and llm: resposta = llm.invoke(prompt.format(question=pergunta)).strip()
            else: resposta = "A minha ligação à Cloud falhou e o meu núcleo local está desativado."
    else:
        if not modo_cloud_ativo and llm:
            print("[🔋] A usar processamento local...")
            resposta = llm.invoke(prompt.format(question=pergunta)).strip()
        else:
            resposta = "Erro: Sem internet, sem API Key, e o processamento local está desligado."

    eel.responder_no_ecra(resposta, cfg['ai_name'])
    if usou_voz: falar_texto(resposta, bloqueante=True)

# --- AUDIÇÃO ---
audio_queue = queue.Queue()
def escutar():
    modelo = Model(get_path("modelos_voz/vosk-model-small-pt-0.3"))
    rec = KaldiRecognizer(modelo, 16000)
    stream = sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=lambda i,f,t,s: audio_queue.put(bytes(i)))

    with stream:
        while True:
            cfg = load_config()
            gatilho = cfg['wake_word'].lower()
            dados = audio_queue.get()
            if rec.AcceptWaveform(dados):
                texto = json.loads(rec.Result()).get("text", "").lower()
                if gatilho in texto:
                    cmd = texto.replace(gatilho, "").strip()
                    if len(cmd) > 1:
                        stream.stop()
                        eel.mostrar_pergunta_mestre(cmd)
                        processar_pergunta(cmd, usou_voz=True)
                        while not audio_queue.empty(): audio_queue.get_nowait()
                        rec.Reset(); stream.start()

# ==========================================
# 5. ARRANQUE DA INTERFACE GRÁFICA (APP)
# ==========================================
threading.Thread(target=escutar, daemon=True).start()

try:
    # Tenta forçar a abertura como uma "App" de Desktop
    print("[🖥️] Marianaa > A invocar interface gráfica...")
    eel.start('index.html', size=(1200, 800))
except EnvironmentError:
    # Failsafe: Se o Linux não encontrar o Chrome/Edge, abre no navegador padrão
    print("[⚠️] Marianaa > Chrome não detetado. A abrir no navegador padrão...")
    eel.start('index.html', mode='default', size=(1200, 800))
