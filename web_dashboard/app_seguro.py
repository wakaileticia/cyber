import os
import psycopg2
from flask import Flask, request, jsonify, abort

app = Flask(__name__)

# Configurações de ligação à base de dados
DB_HOST = os.environ.get("DB_HOST", "localhost")
# RT-08: Utilização de utilizador com privilégios mínimos (least privilege) em vez do admin
DB_USER = os.environ.get("DB_USER", "app_user") 
DB_PASS = os.environ.get("DB_PASS", "app_password")
DB_NAME = os.environ.get("DB_NAME", "vila_aurora_db")

def obter_conexao_db():
    """Estabelece ligação com privilégios limitados à base de dados PostgreSQL."""
    return psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)

def verificar_autenticacao_mfa(token_mfa, utilizador):
    """
    Simula a validação de Autenticação Multifator (MFA) (RT-09)[cite: 4].
    Num ambiente real, validaria contra um servidor TOTP ou envio fora de banda[cite: 4].
    """
    if not token_mfa or len(token_mfa) != 6:
        return False
    return True

def verificar_rbac(utilizador, role_requerida):
    """
    Verifica os perfis de acesso (RBAC) (RT-09)[cite: 4].
    Perfis válidos: operador, técnico, coordenação e auditor[cite: 4].
    """
    # Mapeamento fictício para efeitos de protótipo
    perfis = {
        "maria_voluntaria": "operador",
        "joao_ti": "técnico",
        "ana_coord": "coordenação",
        "carlos_audit": "auditor"
    }
    role_utilizador = perfis.get(utilizador)
    return role_utilizador == role_requerida

@app.route('/')
def index():
    return "Painel de Supervisão - Rede Comunitária Vila Aurora (Seguro)"

@app.route('/api/historico_acessos', methods=['GET'])
def historico_acessos_seguro():
    """
    Endpoint corrigido contra SQL Injection (RT-08)[cite: 4] e protegido por RBAC/MFA (RT-09)[cite: 4].
    """
    utilizador = request.headers.get('X-User')
    token_mfa = request.headers.get('X-MFA-Token')
    termo_busca = request.args.get('busca', '')

    # RT-09: Verificação MFA e RBAC[cite: 4]
    if not verificar_autenticacao_mfa(token_mfa, utilizador):
        abort(401, description="Falha na autenticação MFA.")
        
    if not verificar_rbac(utilizador, "auditor") and not verificar_rbac(utilizador, "coordenação"):
        abort(403, description="Acesso negado. Perfil insuficiente para consultar histórico.")

    # RT-08: Validação de entrada no servidor[cite: 4]
    if not termo_busca.isalnum() and termo_busca != "":
        abort(400, description="Formato de busca inválido. Apenas caracteres alfanuméricos são permitidos.")

    conn = None
    cur = None
    try:
        conn = obter_conexao_db()
        cur = conn.cursor()
        
        # CORREÇÃO RT-08: Utilização de consultas parametrizadas (elimina SQL Injection)[cite: 4]
        query = "SELECT data_acesso, usuario, acao FROM log_acessos WHERE usuario = %s"
        cur.execute(query, (termo_busca,)) # O driver encarrega-se da correta sanitização
        
        resultados = cur.fetchall()
        
        return jsonify({
            "status": "sucesso",
            "dados": resultados
        })
        
    except Exception as e:
        # CORREÇÃO RT-08: Mensagens de erro genéricas sem vazamento de detalhes técnicos[cite: 4]
        app.logger.error(f"Erro interno na base de dados: {str(e)}") # Registo interno em log para o SIEM
        return jsonify({
            "status": "erro",
            "mensagem": "Ocorreu um erro interno ao processar o seu pedido. A equipa técnica foi notificada."
        }), 500
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    # Roda na porta 8443, acessível apenas via VPN (RT-06)[cite: 4]
    app.run(host='0.0.0.0', port=8443)