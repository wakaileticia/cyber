#!/bin/bash
# ==============================================================================
# SCRIPT DE GERAÇÃO DE CERTIFICADOS mTLS (OpenSSL)
# Cumpre o requisito RT-04: Identidade única por dispositivo sem segredo partilhado[cite: 4].
# ==============================================================================

# Cria a pasta caso não exista e entra nela
mkdir -p edge_node/mqtt_broker/certs
cd edge_node/mqtt_broker/certs || exit

echo "A gerar Autoridade Certificadora (CA) do Projeto Vila Aurora..."
# 1. Gerar a CA (Certificate Authority)
openssl req -new -x509 -days 365 -extensions v3_ca -keyout ca.key -out ca.crt -nodes -subj "/C=BR/ST=SP/L=SerraClara/O=RedeVilaAurora/CN=VilaAuroraCA"

echo "A gerar certificado do Servidor MQTT (Broker)..."
# 2. Gerar Certificado do Broker
openssl genrsa -out mqtt_server.key 2048
openssl req -new -out mqtt_server.csr -key mqtt_server.key -subj "/C=BR/ST=SP/L=SerraClara/O=RedeVilaAurora/CN=mqtt_broker"
openssl x509 -req -in mqtt_server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out mqtt_server.crt -days 365

echo "A gerar certificado do Nó de Borda (Buffer Store-and-Forward)..."
# 3. Gerar Certificado do Cliente: Edge Node
openssl genrsa -out edge_node.key 2048
openssl req -new -out edge_node.csr -key edge_node.key -subj "/C=BR/ST=SP/L=SerraClara/O=RedeVilaAurora/CN=edge_node"
openssl x509 -req -in edge_node.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out edge_node.crt -days 365

echo "A gerar certificado da IA Defensiva (Isolation Forest)..."
# 4. Gerar Certificado do Cliente: IA Node
openssl genrsa -out ia_node.key 2048
openssl req -new -out ia_node.csr -key ia_node.key -subj "/C=BR/ST=SP/L=SerraClara/O=RedeVilaAurora/CN=ia_detector"
openssl x509 -req -in ia_node.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out ia_node.crt -days 365

# Ajustar permissões para os contentores conseguirem ler os ficheiros
chmod 644 *.crt *.key
rm *.csr # Removemos os ficheiros de requisição, já não são necessários

echo "=============================================================================="
echo "SUCESSO! Certificados criados na pasta edge_node/mqtt_broker/certs/"
echo "O Broker MQTT já pode ser iniciado com mTLS estrito."
echo "=============================================================================="