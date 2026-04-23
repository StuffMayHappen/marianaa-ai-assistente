const translations = {
    pt: { welcome: "SISTEMA ONLINE. Diz-me o que queres, mestre.", placeholder: "Escreve ou fala...", save: "GUARDAR E REINICIAR", btn: "ENVIAR" },
    en: { welcome: "SYSTEM ONLINE. Tell me what you need, master.", placeholder: "Type or speak...", save: "SAVE & RESTART", btn: "SEND" }
};

let currentAIName = "Marianaa";

// ==========================================
// 1. LÓGICA DE CONFIGURAÇÃO (O CÉREBRO)
// ==========================================
async function loadConfig() {
    try {
        const config = await eel.get_config()();
        currentAIName = config.ai_name;
        
        // Aplicar Cor e Nome
        document.documentElement.style.setProperty('--accent-color', config.accent_color);
        document.getElementById('display-name').innerHTML = `${currentAIName.slice(0,-2)}<span class="purple-text">${currentAIName.slice(-2)}</span>`;
        
        // Preencher os inputs do modal
        document.getElementById('cfg-ai-name').value = config.ai_name;
        document.getElementById('cfg-wake-word').value = config.wake_word;
        document.getElementById('cfg-color').value = config.accent_color;
        document.getElementById('cfg-lang').value = config.language;
        
        // Aplicar Tema
        document.body.className = config.theme + '-theme';
        
        // Aplicar Idioma
        const t = translations[config.language] || translations['pt'];
        document.getElementById('welcome-msg').innerText = t.welcome;
        document.getElementById('user-input').placeholder = t.placeholder;
        document.getElementById('save-settings').innerText = t.save;
        document.getElementById('submit-btn').innerText = t.btn;
    } catch (e) {
        console.error("Erro fatal ao ligar ao Python para definições:", e);
    }
}

// Arranca o carregamento assim que o JS liga
loadConfig();

// ==========================================
// 2. CONTROLO DA INTERFACE E MODAL
// ==========================================
const modal = document.getElementById('settings-modal');
const openBtn = document.getElementById('open-settings');

if (openBtn) {
    openBtn.onclick = () => {
        modal.style.display = 'block';
    };
}

window.onclick = (event) => {
    if (event.target == modal) modal.style.display = 'none';
};

document.getElementById('save-settings').onclick = async () => {
    const cfg = {
        ai_name: document.getElementById('cfg-ai-name').value,
        wake_word: document.getElementById('cfg-wake-word').value,
        accent_color: document.getElementById('cfg-color').value,
        language: document.getElementById('cfg-lang').value,
        theme: document.body.classList.contains('light-theme') ? 'light' : 'dark'
    };
    await eel.save_config(cfg)();
    location.reload(); // Reinicia a aba para injetar a nova alma
};

const toggleThemeBtn = document.getElementById('toggle-theme');
if (toggleThemeBtn) {
    toggleThemeBtn.onclick = () => {
        document.body.classList.toggle('light-theme');
        document.body.classList.toggle('dark-theme');
    };
}

// ==========================================
// 3. EFEITOS VISUAIS (A ESTÉTICA)
// ==========================================
document.addEventListener('mousedown', (e) => {
    // Previne o efeito de pedra na água se estiveres a clicar dentro das definições
    if(e.target.closest('.modal-content')) return;

    let ripple = document.createElement('div');
    ripple.className = 'ripple';
    ripple.style.left = (e.clientX - 50) + 'px';
    ripple.style.top = (e.clientY - 50) + 'px';
    ripple.style.width = ripple.style.height = '100px';
    document.body.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
});

const dots = [];
for (let i = 0; i < 15; i++) {
    let dot = document.createElement('div');
    dot.className = 'snake-dot';
    document.body.appendChild(dot);
    dots.push({ x: 0, y: 0, node: dot });
}

let mouseX = 0, mouseY = 0;
document.addEventListener('mousemove', (e) => { mouseX = e.clientX; mouseY = e.clientY; });

function drawSnake() {
    let x = mouseX, y = mouseY;
    dots.forEach((dot, index) => {
        dot.x = x; dot.y = y;
        dot.node.style.left = x + 'px';
        dot.node.style.top = y + 'px';
        const next = dots[index + 1] || dots[0];
        x += (next.x - x) * 0.5; y += (next.y - y) * 0.5;
    });
    requestAnimationFrame(drawSnake);
}
drawSnake();

// ==========================================
// 4. LÓGICA DE CHAT COM O CÉREBRO PYTHON
// ==========================================
const chatBox = document.getElementById('chat-box');
const input = document.getElementById('user-input');
const btn = document.getElementById('submit-btn');

function addMessage(text, sender) {
    let p = document.createElement('p');
    p.className = sender === currentAIName ? 'marianaa-msg' : 'user-msg'; 
    p.innerHTML = `<strong>${sender}:</strong> ${text}`;
    chatBox.appendChild(p);
    chatBox.scrollTop = chatBox.scrollHeight;
}

eel.expose(responder_no_ecra);
function responder_no_ecra(resposta, nome) { 
    addMessage(resposta, nome || currentAIName); 
}

eel.expose(mostrar_pergunta_mestre);
function mostrar_pergunta_mestre(texto) { 
    addMessage(texto, 'Mestre (Voz)'); 
}

if (btn && input) {
    btn.onclick = () => {
        let val = input.value.trim();
        if(val) { 
            addMessage(val, 'Mestre'); 
            input.value = ''; 
            eel.processar_pergunta(val); 
        }
    };
    input.onkeypress = (e) => { 
        if(e.key === 'Enter') btn.onclick(); 
    };
}
