import time
import json
import random
import os
import paho.mqtt.client as mqtt

# Configurações do Broker MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 8883

# Caminho absoluto para a pasta de certificados centralizada (garante que o Python os encontre sem erros)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CA_CERT = os.path.abspath(os.path.join(BASE_DIR, "../mqtt_broker/certs/ca.crt"))
CLIENT_CERT = os.path.abspath(os.path.join(BASE_DIR, "../mqtt_broker/certs/edge_node.crt"))
CLIENT_KEY = os.path.abspath(os.path.join(BASE_DIR, "../mqtt_broker/certs/edge_node.key"))

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Sensor simulado conectado com sucesso ao Broker MQTT via mTLS!")
    else:
        print(f"Falha na conexão. Código de erro: {rc}")

if __name__ == "__main__":
    # Inicializa o cliente MQTT
    client = mqtt.Client()
    
    # Configura a segurança mTLS estrita exigida pelo projeto
# Configura a segurança mTLS estrita
    try:
        client.tls_set(
            ca_certs=CA_CERT, 
            certfile=CLIENT_CERT, 
            keyfile=CLIENT_KEY
        )
        # ADICIONE ESTA LINHA ABAIXO PARA IGNORAR A VERIFICAÇÃO DE HOSTNAME NO LOCALHOST:
        client.tls_insecure_set(True)
        
        print("Certificados mTLS carregados com sucesso.")
    except Exception as e:
        print(f"ERRO CRÍTICO ao carregar certificados: {e}")
        exit(1)
        
    client.on_connect = on_connect
    
    print("A iniciar simulação dos sensores da Vila Aurora...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        while True:
            # Simula a Câmara Fria da UBS (Faixa normal: 4.0°C a 7.5°C)
            temperatura = round(random.uniform(4.0, 7.5), 1)
            payload_ubs = json.dumps({"temperatura": temperatura})
            client.publish("vila_aurora/sensores/ubs/camara_fria", payload_ubs)
            print(f"[Câmara Fria] Enviado: {payload_ubs}")
            
            # Simula o Reservatório de Água (Faixa normal: 65% a 95%)
            nivel = round(random.uniform(65.0, 95.0), 1)
            payload_agua = json.dumps({"nivel": nivel})
            client.publish("vila_aurora/sensores/agua", payload_agua)
            print(f"[Reservatório] Enviado: {payload_agua}")
            
            print("-" * 40)
            time.sleep(5) # Aguarda 5 segundos até a próxima telemetria
            
    except Exception as e:
        print(f"Erro na execução: {e}")
    except KeyboardInterrupt:
        print("\nSimulação encerrada pelo utilizador.")
        client.loop_stop()
        client.disconnect()