#!/bin/bash
# ==============================================================================
# SCRIPT DE RESPOSTA AUTOMATIZADA (SOAR) - BLOQUEIO DE IP
# Cumpre o requisito RT-15: Respostas automatizadas de baixo risco[cite: 5].
# Integrado com o Wazuh Active Response para isolar ameaças em tempo real.
# ==============================================================================

# O Wazuh passa um ficheiro JSON como primeiro argumento contendo os dados do alerta
ALERT_JSON=$1
LOG_FILE="/var/log/active_responses_vila_aurora.log"

# Verifica se o argumento foi fornecido
if [ -z "$ALERT_JSON" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERRO: Nenhum dado de alerta fornecido." >> $LOG_FILE
    exit 1
fi

# Extrai o IP de origem do JSON do alerta usando jq (dependência do sistema)
SRC_IP=$(jq -r .parameters.alert.data.srcip "$ALERT_JSON")

if [ "$SRC_IP" == "null" ] || [ -z "$SRC_IP" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERRO: IP de origem não encontrado no alerta." >> $LOG_FILE
    exit 1
fi

# ------------------------------------------------------------------------------
# EXECUÇÃO DE AÇÃO DE BAIXO RISCO (RT-15)[cite: 5]
# Bloqueia o IP ofensivo na firewall iptables
# ------------------------------------------------------------------------------
iptables -I INPUT -s "$SRC_IP" -j DROP
iptables -I FORWARD -s "$SRC_IP" -j DROP

echo "$(date '+%Y-%m-%d %H:%M:%S') - SUCESSO: IP $SRC_IP bloqueado via Active Response." >> $LOG_FILE

# ------------------------------------------------------------------------------
# NOTA SOBRE AÇÕES DE ALTO IMPACTO (RT-15)[cite: 5]
# Ações como desligar a bomba de água do abrigo ou abrir fechaduras eletrónicas 
# NÃO estão automatizadas neste SOAR. Exigem intervenção e aprovação humana[cite: 5].
# ------------------------------------------------------------------------------