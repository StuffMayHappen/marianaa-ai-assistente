import os
import warnings
import glob
import shutil
from langchain_community.llms import LlamaCpp
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

# Silenciador de avisos para manter o terminal limpo
os.environ["HF_HUB_OFFLINE"] = "1"
warnings.filterwarnings("ignore")

print("[🔥] Marianaa > Arquitetura RAG de Elite (Pasta 'docs' Ativada)")

# 1. Configurações de Sistema (Monstro 8B)
MODEL_PATH = "models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
PASTA_DOCS = "docs"
ARQUIVO_BASE = "docs/base_conhecimento.txt"
DB_DIR = "chroma_db"

# 2. Setup do Sistema de Ficheiros
os.makedirs(PASTA_DOCS, exist_ok=True)

# Criar a base de conhecimento se não existir (Atualizado para 32GB de RAM)
if not os.path.exists(ARQUIVO_BASE):
    with open(ARQUIVO_BASE, "w", encoding="utf-8") as f:
        f.write("INFORMAÇÃO CONFIDENCIAL:\nO mestre Walter utiliza um ASUS ROG Strix com Ryzen 7 4800H, 32GB de RAM e uma RTX 3050. A Marianaa é a sua IA principal, génia e sarcástica.")

# 3. Leitura Genial e Recursiva
print(f"[📚] Marianaa > A varrer a pasta '{PASTA_DOCS}' e subpastas...")
ficheiros = glob.glob(f"{PASTA_DOCS}/**/*.txt", recursive=True) + \
            glob.glob(f"{PASTA_DOCS}/**/*.md", recursive=True)

documentos = []
for f_path in ficheiros:
    try:
        loader = TextLoader(f_path, encoding="utf-8")
        documentos.extend(loader.load())
    except Exception as e:
        print(f"[!] Erro ao ler {f_path}: {e}")

# Fragmentação de conhecimento para a VRAM
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
textos_divididos = text_splitter.split_documents(documentos)

# 4. Memória Vetorial (ChromaDB)
print("[🧠] Marianaa > A limpar a memória antiga e a re-indexar conhecimento...")

# A Bomba de Limpeza: Aniquila os clones antigos
if os.path.exists(DB_DIR):
    shutil.rmtree(DB_DIR) 

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Cria a base de dados limpa e fresca a partir do zero
vectorstore = Chroma.from_documents(documents=textos_divididos, embedding=embeddings, persist_directory=DB_DIR)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 5. Motor de Inferência (8B Híbrido)
print("[⚡] Marianaa > A carregar o Monstro 8B (16 Camadas GPU)...")
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

# 6. Prompt de Engenharia (Llama 3 Style)
template = """<|start_header_id|>system<|end_header_id|>
És a Marianaa, uma IA genial e sarcástica. Responde usando APENAS o contexto abaixo. 
Se não souberes, sê honesta e sê direta ao Walter.
Contexto: {context}<|eot_id|><|start_header_id|>user<|end_header_id|>
{question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

PROMPT = PromptTemplate(template=template, input_variables=["context", "question"])

def formatar_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# 7. Chain Moderna (LCEL)
qa_chain = (
    {"context": retriever | formatar_docs, "question": RunnablePassthrough()}
    | PROMPT
    | llm
    | StrOutputParser()
)

# 8. Teste de Validação
pergunta = "Qual é o hardware atual do mestre e o que sabes sobre os projetos na pasta docs?"
print(f"\n[?] Pergunta: {pergunta}")
print("[🔎] Marianaa > A processar...\n")

resposta = qa_chain.invoke(pergunta)

print("--- RESPOSTA DA IA ---")
print(resposta.strip())
print("----------------------")
