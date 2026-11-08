import json
import time
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix
import paho.mqtt.client as mqtt

# Configurações MQTT
MQTT_BROKER = "mqtt_broker"
MQTT_PORT = 8883
MQTT_TOPIC = "vila_aurora/sensores/ubs/camara_fria"
ALERT_TOPIC = "vila_aurora/alertas/anomalia"

def gerar_dados_sinteticos_treino():
    """
    Gera dados sintéticos (apenas dados fictícios, conforme exigido em proteção de privacidade[cite: 4, 9])
    para treinar o modelo. Simula o funcionamento normal da câmara fria da UBS (2°C a 8°C).
    """
    np.random.seed(42)
    # 95% dados normais (temperatura entre 2 e 8)
    dados_normais = np.random.normal(loc=5.0, scale=1.0, size=(950, 1))
    # 5% dados anómalos (falha de energia, porta aberta)
    dados_anomalos = np.random.uniform(low=9.0, high=25.0, size=(50, 1))
    
    X = np.vstack([dados_normais, dados_anomalos])
    y_verdadeiro = np.array([1] * 950 + [-1] * 50) # 1 normal, -1 anomalia
    
    return pd.DataFrame(X, columns=['temperatura']), y_verdadeiro

def treinar_modelo_e_extrair_metricas():
    """Treina o modelo Isolation Forest e imprime as métricas (RT-16)[cite: 4]."""
    print("A treinar modelo Isolation Forest...")
    X_treino, y_verdadeiro = gerar_dados_sinteticos_treino()
    
    # Modelo Isolation Forest para detecção de anomalias na telemetria[cite: 4]
    modelo = IsolationForest(contamination=0.05, random_state=42)
    modelo.fit(X_treino)
    
    # Previsões para gerar métricas de desempenho[cite: 4]
    y_pred = modelo.predict(X_treino)
    
    print("\n--- Métricas do Modelo IA (RT-16) ---")
    print(classification_report(y_verdadeiro, y_pred, target_names=['Anomalia', 'Normal']))
    
    tn, fp, fn, tp = confusion_matrix(y_verdadeiro, y_pred).ravel()
    print(f"Falsos Positivos (Alarmes falsos): {fp}")
    print(f"Precisão na deteção: {tp / (tp + fp):.2f}")
    print(f"Revocação (Recall): {tp / (tp + fn):.2f}")
    print("-------------------------------------\n")
    
    return modelo

# Inicializar e treinar o modelo globalmente
modelo_ia = treinar_modelo_e_extrair_metricas()

def on_connect(client, userdata, flags, rc):
    print(f"IA conectada ao MQTT Broker (Código: {rc})")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    """Analisa a telemetria em tempo real para detetar anomalias no ambiente."""
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        temperatura_atual = payload.get("temperatura")
        
        if temperatura_atual is not None:
            # Prever se o dado atual é anómalo
            df_atual = pd.DataFrame({'temperatura': [temperatura_atual]})
            previsao = modelo_ia.predict(df_atual)[0]
            
            if previsao == -1:
                alerta = {
                    "origem": "ia_detector",
                    "tipo": "ANOMALIA_TEMPERATURA",
                    "valor": temperatura_atual,
                    "timestamp": time.time(),
                    "severidade": "ALTA"
                }
                # Publicar alerta para o SIEM/Supervisão[cite: 4]
                client.publish(ALERT_TOPIC, json.dumps(alerta))
                print(f"[ALERTA IA] Temperatura anómala detetada: {temperatura_atual}°C!")
            else:
                print(f"[NORMAL] Leitura atual: {temperatura_atual}°C")
    except json.JSONDecodeError:
        pass

if __name__ == "__main__":
    client = mqtt.Client()
    
    # RT-04: Conexão via mTLS[cite: 4]
    try:
        client.tls_set(
            ca_certs="/mosquitto/config/certs/ca.crt", 
            certfile="/mosquitto/config/certs/ia_node.crt", 
            keyfile="/mosquitto/config/certs/ia_node.key"
        )
    except FileNotFoundError:
        print("AVISO: Executar sem mTLS (apenas para ambiente de desenvolvimento local).")
        
    client.on_connect = on_connect
    client.on_message = on_message
    
    print("A iniciar monitorização em tempo real de telemetria...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"Erro ao conectar ao MQTT: {e}")