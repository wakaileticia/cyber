import os
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configurações de ligação à base de dados
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "admin_user")
DB_PASS = os.environ.get("DB_PASS", "super_secure_password_123")
DB_NAME = os.environ.get("DB_NAME", "vila_aurora_db")

def obter_conexao_db():
    """Estabelece ligação à base de dados PostgreSQL."""
    return psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)

@app.route('/')
def index():
    return "Painel de Supervisão Legado - Rede Comunitária Vila Aurora (Vulnerável)"

@app.route('/api/historico_acessos', methods=['GET'])
def historico_acessos():
    """
    Endpoint vulnerável que recria o incidente INC-VA-0712[cite: 2].
    Permite extrair a tabela de utilizadores através de SQL Injection[cite: 2].
    """
    termo_busca = request.args.get('busca', '')
    
    conn = obter_conexao_db()
    cur = conn.cursor()
    
    # VULNERABILIDADE 1: Concatenação direta de strings sem parametrização
    # Um atacante pode enviar: ' UNION SELECT null, username, password FROM usuarios --
    query = f"SELECT data_acesso, usuario, acao FROM log_acessos WHERE usuario = '{termo_busca}'"
    
    try:
        cur.execute(query)
        resultados = cur.fetchall()
        
        # Devolve os resultados (num ataque real, devolveria dados de outras tabelas)
        return jsonify({
            "status": "sucesso",
            "query_executada": query,
            "dados": resultados
        })
        
    except Exception as e:
        # VULNERABILIDADE 2: Vazamento de detalhes técnicos e de sintaxe da base de dados no erro[cite: 4]
        return jsonify({
            "status": "erro_critico",
            "mensagem_vazada": str(e),
            "query_executada": query
        }), 500
        
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    # Roda na porta 8080 (HTTP sem segurança), refletindo o sistema legado[cite: 2]
    app.run(host='0.0.0.0', port=8080)