import paho.mqtt.client as mqtt
import sqlite3
import time
import json
import threading
import requests

# Configurações do MQTT Local (Camada de Borda)
MQTT_BROKER_LOCAL = "mqtt_broker" # Nome do contentor no docker-compose
MQTT_PORT = 8883
MQTT_TOPIC = "vila_aurora/sensores/#"

# Configuração do Servidor Central (Nuvem/Supervisão)
CENTRAL_API_URL = "http://web_dashboard:8080/api/telemetry"
HEALTH_CHECK_URL = "http://web_dashboard:8080/health"

# Configuração do Buffer Local (SQLite)
DB_FILE = "local_buffer.db"

def init_db():
    """Inicializa a base de dados local para operação autónoma (RT-02)"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry_buffer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            payload TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def check_wan_connection():
    """Verifica se há conectividade com a rede central (Simulação de link de fibra)"""
    try:
        response = requests.get(HEALTH_CHECK_URL, timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False

def on_connect(client, userdata, flags, rc):
    print(f"Conectado ao Broker MQTT Local com código {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    """Callback executado ao receber dados dos sensores/atuadores"""
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    
    # Salva a mensagem no buffer local IMEDIATAMENTE (Garante operação autónoma)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO telemetry_buffer (topic, payload) VALUES (?, ?)", (topic, payload))
    conn.commit()
    conn.close()
    
    print(f"[{time.strftime('%H:%M:%S')}] Dado guardado localmente (topic: {topic})")

def forwarder_task():
    """Thread em background que esvazia o buffer quando a WAN é restabelecida"""
    while True:
        if check_wan_connection():
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            # Lê em lotes para não sobrecarregar a rede no momento da reconciliação
            cursor.execute("SELECT id, topic, payload, timestamp FROM telemetry_buffer ORDER BY id ASC LIMIT 50")
            rows = cursor.fetchall()
            
            if rows:
                print(f"Ligação restaurada! A reconciliar {len(rows)} registos pendentes...")
                for row in rows:
                    record_id, topic, payload, timestamp = row
                    data = {
                        "topic": topic,
                        "payload": json.loads(payload) if payload.startswith('{') else payload,
                        "timestamp": timestamp
                    }
                    
                    try:
                        # Envia para a nuvem/servidor central
                        res = requests.post(CENTRAL_API_URL, json=data, timeout=3)
                        if res.status_code == 200:
                            # Remove do buffer APENAS se o envio for bem-sucedido (store-and-forward real)
                            cursor.execute("DELETE FROM telemetry_buffer WHERE id=?", (record_id,))
                            conn.commit()
                    except requests.RequestException:
                        print("Falha ao enviar registo, WAN instável. A abortar reconciliação atual.")
                        break # Para o loop para tentar novamente no próximo ciclo
            conn.close()
        
        time.sleep(5) # Aguarda 5 segundos antes da próxima verificação

if __name__ == "__main__":
    init_db()
    
    # Inicia a thread de reconciliação em background
    threading.Thread(target=forwarder_task, daemon=True).start()
    
    # Inicia o cliente MQTT
    client = mqtt.Client()
    
    # RT-04: Identidade e Criptografia (mTLS). 
    # Os certificados gerados pela CA do projeto devem ser mapeados aqui.
    try:
        client.tls_set(
            ca_certs="/mosquitto/config/certs/ca.crt", 
            certfile="/mosquitto/config/certs/edge_node.crt", 
            keyfile="/mosquitto/config/certs/edge_node.key"
        )
    except FileNotFoundError:
        print("AVISO: Certificados mTLS não encontrados. A iniciar sem TLS para testes locais.")
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    while True:
        try:
            client.connect(MQTT_BROKER_LOCAL, MQTT_PORT, 60)
            client.loop_forever()
        except Exception as e:
            print(f"Erro de ligação com o broker MQTT: {e}. A tentar novamente em 5s...")
            time.sleep(5)