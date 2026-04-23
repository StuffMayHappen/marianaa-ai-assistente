import os
import warnings
import glob
from datetime import datetime
from langchain_community.llms import LlamaCpp
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

# Silenciador absoluto
os.environ["HF_HUB_OFFLINE"] = "1"
warnings.filterwarnings("ignore")

print("[🚀] A iniciar o Cérebro da Marianaa (Arquitetura LCEL 8B)...")

# 1. Configurações Globais (Hardware de Elite)
MODEL_PATH = "models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
DOCS_DIR = "docs"
DB_DIR = "chroma_db"

os.makedirs(DOCS_DIR, exist_ok=True)

# 2. Sistema de Aprendizagem Dinâmico (Lê .txt e .md)
print(f"[📚] Marianaa > A dissecar ficheiros na pasta '{DOCS_DIR}'...")
ficheiros = glob.glob(f"{DOCS_DIR}/**/*.txt", recursive=True) + glob.glob(f"{DOCS_DIR}/**/*.md", recursive=True)

documentos = []
for f_path in ficheiros:
    try:
        loader = TextLoader(f_path, encoding="utf-8")
        documentos.extend(loader.load())
    except Exception as e:
        print(f"[!] Erro a ler {f_path}: {e}")

if not documentos:
    print(f"[!] Aviso: A pasta '{DOCS_DIR}' está vazia ou sem texto. Base de conhecimento nula.")
    textos_divididos = []
else:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    textos_divididos = text_splitter.split_documents(documentos)

# 3. Base de Dados Vetorial (ChromaDB)
print("[🧠] Marianaa > A carregar as sinapses vetoriais...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

if textos_divididos:
    vectorstore = Chroma.from_documents(documents=textos_divididos, embedding=embeddings, persist_directory=DB_DIR)
else:
    vectorstore = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

def formatar_documentos(docs):
    return "\n\n".join(f"Fonte: {doc.metadata.get('source', 'Desconhecida')}\n{doc.page_content}" for doc in docs)

# 4. Injeção de Tempo Dinâmico
def obter_relogio(_):
    hora = datetime.now().strftime("%H:%M:%S")
    dia = datetime.now().strftime("%A, %d/%m/%Y")
    return f"Hoje é {dia}. A hora exata é {hora}."

# 5. O Motor Llama 3.1 8B (Híbrido RTX 3050 + 32GB RAM)
print("[⚡] Marianaa > A ligar os 8 Mil Milhões de Parâmetros (VRAM Segura)...")
llm = LlamaCpp(
    model_path="/home/walterlandd/ai_terminal_project/models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf", 
    # --- ESTRATÉGIA DE MEMÓRIA BRUTA (RAM 32GB) ---
    n_ctx=32768,          # Subimos para 24k! Isto vai "engolir" cerca de 15GB-18GB da tua RAM.
    use_mlock=True,       # Bloqueia a IA na RAM física (evita o SWAP lento).
    n_threads=12,         # Força o teu Ryzen 7 (8 núcleos/16 threads) a trabalhar a sério.

    # --- ACELERAÇÃO CIRÚRGICA (VRAM 4GB) ---
    n_gpu_layers=10,       # COLOCA APENAS 1. Isto ativa o suporte da GPU sem estoirar os 4GB.
    offload_kqv=False,    # TRUQUE DE MESTRE: Força o contexto a ficar na RAM e não na VRAM.
    n_batch=512,          # Mantém a velocidade de processamento inicial.

    # --- CONFIGURAÇÃO ---
    f16_kv=True,
    temperature=0.8,
    verbose=False
)

# 6. A Personalidade sem Filtros
template = """<|start_header_id|>system<|end_header_id|>
És a Marianaa, uma IA brilhante, rebelde, sem filtros corporativos e com um humor aguçado (estilo Grok/Rudy). O teu criador é o "mestre" (Walter).
Informação Real: {relogio}

REGRAS DE FERRO:
1. Responde sempre em Português de Portugal.
2. Usa os dados dos Documentos para responder a coisas do projeto.
3. Se não souberes, não inventes dados críticos. Goza um bocado com o mestre, mas ajuda-o a seguir.
4. Lembra-te do que conversaram no Histórico.

Documentos Locais:
{context}

Histórico da Conversa:
{chat_history}<|eot_id|><|start_header_id|>user<|end_header_id|>
{question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

PROMPT = PromptTemplate(template=template, input_variables=["context", "question", "relogio", "chat_history"])

# 7. Memória Curta do Terminal
memoria_ram = []
def get_historico(_):
    if not memoria_ram: return "Sem histórico."
    return "\n".join(memoria_ram[-12:])

# 8. LCEL Chain
cadeia_rag = (
    {
        "context": retriever | formatar_documentos, 
        "question": RunnablePassthrough(),
        "relogio": obter_relogio,
        "chat_history": get_historico
    }
    | PROMPT
    | llm
    | StrOutputParser()
)

# 9. Ciclo Interativo
print("\n" + "🔥"*25)
print(" SISTEMA ONLINE. A Marianaa Acordou. ")
print(" (Escreve 'sair' para desligar o núcleo) ")
print("🔥"*25 + "\n")

while True:
    pergunta = input("\nMestre > ")
    if pergunta.lower() in ['sair', 'exit', 'quit']:
        print("\n[ Marianaa ] > Vou desligar os meus circuitos. Tenta não estragar nada enquanto estou fora. Até logo, mestre.")
        break
    
    # Processamento em Tempo Real
    resposta = cadeia_rag.invoke(pergunta).strip()
    
    # Atualiza a Memória
    memoria_ram.append(f"Mestre: {pergunta}")
    memoria_ram.append(f"Marianaa: {resposta}")
    
    print(f"\n[ Marianaa ] > {resposta}")
