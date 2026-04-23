import os, json, queue, threading, wave, subprocess, time, io, urllib.request, asyncio, sys, base64, webbrowser
from datetime import datetime
import eel, sounddevice as sd, numpy as np, edge_tts, speech_recognition as sr
from rag_ia import consultar_documentos, indexar_documentos # Importa as funções de memória
from vosk import Model, KaldiRecognizer, SetLogLevel
from langchain_community.llms import LlamaCpp
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI # <--- O CONECTOR DA CLOUD

# ==========================================
# GESTÃO DE CAMINHOS DINÂMICOS E INTERNET
# ==========================================
def get_path(rel_path):
    # O PyInstaller esconde a interface 'web' na pasta secreta _internal
    if rel_path.startswith("web") and hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, rel_path)
    
    # As outras pastas (models, modelos_voz, config) ficam na pasta normal
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), rel_path)
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), rel_path)

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

# --- CORDAS VOCAIS (TRANSMISSÃO REDE/BASE64) ---
def falar_texto(texto, bloqueante=False):
    cfg = load_config()
    async def amain():
        voice = "pt-PT-RaquelNeural" if cfg['language'] == "pt" else "en-US-AvaNeural"
        communicate = edge_tts.Communicate(texto, voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": 
                audio_data += chunk["data"]
        
        if audio_data:
            # Empacotar o áudio gerado para viajar pela rede Wi-Fi
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            # Dar a ordem ao navegador (PC ou Telemóvel) para tocar
            eel.tocar_audio_no_navegador(audio_b64)()

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
    
    # --- FASE 1: CONSULTAR PROJETOS (RAG) ---
    print(f"[📚] Marianaa > A pesquisar nos teus projetos por: {pergunta}")
    contexto_projeto = consultar_documentos(pergunta)
    
    if contexto_projeto:
        print("[💡] Marianaa > Encontrei informação nos teus documentos!")
        instrucao_contexto = f"\n\nUsa esta informação dos documentos do mestre para responder: {contexto_projeto}"
    else:
        instrucao_contexto = ""

    # --- FASE 2: PREPARAR O PROMPT ---
    template = f"<|start_header_id|>system<|end_header_id|>\nÉs a {cfg['ai_name']}. Responde de forma curta e sarcástica.{instrucao_contexto}<|eot_id|><|start_header_id|>user<|end_header_id|>{{question}}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
    prompt = PromptTemplate(template=template, input_variables=["question"])
    
    resposta = ""
    
    # --- FASE 3: GERAR RESPOSTA (Cloud ou Local) ---
    if api_key and tem_internet():
        try:
            print("[☁️] A processar na Cloud...")
            cloud_llm = ChatOpenAI(
                openai_api_base="https://openrouter.ai/api/v1", 
                openai_api_key=api_key,
                model_name="google/gemma-2-9b-it:free", 
                max_tokens=500, # Aumentei para caber a análise do projeto
                temperature=0.7
            )
            resposta = cloud_llm.invoke(prompt.format(question=pergunta)).content.strip()
        except Exception as e:
            print(f"[⚠️] Cloud falhou: {e}")
            if not modo_cloud_ativo and llm: resposta = llm.invoke(prompt.format(question=pergunta)).strip()
            else: resposta = "A minha ligação à Cloud falhou e não consegui aceder ao meu núcleo local."
    else:
        if not modo_cloud_ativo and llm:
            print("[🔋] A usar processamento local...")
            resposta = llm.invoke(prompt.format(question=pergunta)).strip()
        else:
            resposta = "Erro: Estou sem acesso a qualquer cérebro de momento."

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

# ---> A MARIANAA ESTUDA OS TEUS FICHEIROS AQUI <---
try:
    print("[📚] Marianaa > A ler e a memorizar os teus documentos da pasta docs/...")
    indexar_documentos()
except Exception as e:
    print(f"[⚠️] Marianaa > Erro a memorizar documentos: {e}")

def abrir_modo_app():
    time.sleep(1.5) # Dá tempo para a porta 8000 acordar
    print("[🖥️] Marianaa > A forçar o navegador a abrir em Modo App (sem barras)...")
    
    # Comandos para atacar os navegadores do Linux e forçar o Modo App
    cmd_brave = "brave-browser --app=http://127.0.0.1:8000 >/dev/null 2>&1"
    cmd_flatpak = "flatpak run com.brave.Browser --app=http://127.0.0.1:8000 >/dev/null 2>&1"
    cmd_chrome = "google-chrome --app=http://127.0.0.1:8000 >/dev/null 2>&1"
    
    # Tenta um a um até a janela saltar!
    if os.system(cmd_flatpak) != 0:
        if os.system(cmd_brave) != 0:
            os.system(cmd_chrome)

try:
    print("[🖥️] Marianaa > A invocar interface...")
    eel.start('index.html', host='0.0.0.0', port=8000, size=(1200, 800))
except EnvironmentError:
    print("[⚠️] Marianaa > Blindagem do Linux detetada. A usar força bruta de Janela App...")
    threading.Thread(target=abrir_modo_app, daemon=True).start()
    eel.start('index.html', host='0.0.0.0', port=8000, mode=None)

