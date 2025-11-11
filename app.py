import os  # <<<< NOVA IMPORTAÇÃO
from flask import Flask, render_template, request, session, redirect, url_for
from google import genai
from google.genai.errors import APIError

# =========================================================================
# === CONFIGURAÇÃO (CHAVE DE API) ===
# =========================================================================
# 💡 IMPORTANTE: Agora, a chave é lida da variável de ambiente no servidor Render.
# Se a chave não for encontrada (o que causa o Erro 500), ela será None.
API_KEY = os.environ.get("GEMINI_API_KEY") 

try:
    # A variável API_KEY será lida da configuração do Render.
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    # Se o cliente falhar ao iniciar (geralmente por chave ausente), definimos como None
    print(f"Erro ao inicializar o cliente Gemini: {e}")
    client = None

# Configuração da aplicação Flask
app = Flask(__name__)
app.secret_key = 'fishgpt_chave_secreta_longa_e_unica' 

# =========================================================================
# === LÓGICA DE BUSCA DE IMAGEM (PLACEHOLDER) ===
# =========================================================================
def buscar_imagem(peixe_nome):
    """
    Simula a busca de imagem.
    """
    if "tucunaré" in peixe_nome.lower():
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Cichla_ocellaris_2.jpg/450px-Cichla_ocellaris_2.jpg"
    
    return f"https://source.unsplash.com/400x300/?{peixe_nome},fishing" 

# =========================================================================
# === FUNÇÃO CENTRAL DA API (Lógica de Prompt) ===
# =========================================================================
def requisitar_informacoes(peixe_nome, tipo_info="basico"):
    """Faz a requisição à Gemini API com o prompt formatado."""
    # Garante que o cliente existe antes de tentar a chamada
    if not client:
        return "❌ Erro na API: O cliente Gemini não foi configurado (Verifique a GEMINI_API_KEY no Render)."
        
    if tipo_info == "basico":
        prompt_text = "Forneça as informações BÁSICAS (NOME, STATUS DE EXTINÇÃO (IUCN), REGULAMENTAÇÃO (BR)) para o peixe."
    else:
        prompt_text = "Forneça as informações DETALHADAS (VARIAÇÃO DE PESCA, MELHOR ÉPOCA/CLIMA, ISCA RECOMENDADA, VARAS/EQUIPAMENTO) de pesca para o peixe."
    
    prompt = f"{prompt_text} Nome do peixe: {peixe_nome}. Formate a resposta usando **Markdown** para ser exibida em HTML. Use títulos e negrito para clareza."

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"❌ Erro na API: Não foi possível obter as informações. Detalhes: {e}"


# =========================================================================
# === ROTA 1: BUSCA ESTRUTURADA (/) ===
# =========================================================================
@app.route('/', methods=['GET', 'POST'])
def index():
    # ... (código inalterado)
    info = None
    peixe_nome = None
    image_url = None
    
    if request.method == 'POST':
        peixe_nome = request.form.get('peixe')
        action = request.form.get('action')

        if peixe_nome:
            image_url = buscar_imagem(peixe_nome) 
            
            if action == 'buscar_basico':
                info = requisitar_informacoes(peixe_nome, "basico")
            elif action == 'buscar_detalhes':
                info = requisitar_informacoes(peixe_nome, "detalhado")

    return render_template('index.html', info=info, peixe_nome=peixe_nome, image_url=image_url)


# =========================================================================
# === ROTA 2: CHAT CONVERSACIONAL (/chat) ===
# =========================================================================
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    # ... (código inalterado)
    # 1. Gerencia a Sessão (Histórico)
    if 'chat_session' not in session:
        if not client:
            session['chat_history'] = [{'role': 'ai', 'text': '❌ O cliente Gemini não está disponível para chat. (Verifique a chave de API)'}]
            return render_template('chat.html', history=session.get('chat_history', []))
            
        system_instruction = "Você é um assistente de pesca muito amigável e especialista no Brasil. Suas respostas são focadas em dicas de pesca, regulamentação e biologia marinha. Seu nome é FishGPT."
        
        session['chat_session'] = client.chats.create(
            model='gemini-2.5-flash',
            system_instruction=system_instruction
        )
        session['chat_history'] = []
    
    # 2. Processa a Mensagem do Usuário
    if request.method == 'POST':
        user_message = request.form.get('message')
        
        if user_message and client:
            try:
                chat_session_obj = session['chat_session']
                response = chat_session_obj.send_message(user_message)
                ai_response = response.text
                
                session['chat_history'].append({'role': 'user', 'text': user_message})
                session['chat_history'].append({'role': 'ai', 'text': ai_response})
                session.modified = True 

            except Exception as e:
                session['chat_history'].append({'role': 'ai', 'text': f"❌ Falha de comunicação com a IA. Detalhe: {e}"})
                session.modified = True
                
    return render_template('chat.html', history=session.get('chat_history', []))

# Rota para resetar o chat
@app.route('/reset_chat')
def reset_chat():
    session.pop('chat_session', None)
    session.pop('chat_history', None)
    return redirect(url_for('chat'))

# =========================================================================
# === EXECUÇÃO DO SERVIDOR (Apenas para Terminal/Local) ===
# =========================================================================
if __name__ == '__main__':
    print("\n------------------------------------------------------")
    print("Servidor FishGPT iniciado! (Rodando localmente)")
    print("------------------------------------------------------")
    # Para rodar localmente no Pydroid, descomente a linha abaixo:
    # app.run(host='0.0.0.0', debug=True)
