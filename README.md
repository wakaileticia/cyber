# GS2026.2_4ECS_G01_E2 - Protótipo Funcional: Resilient Community Infrastructure

Este repositório contém a infraestrutura computacional segura e resiliente da Rede Comunitária Vila Aurora, desenvolvida para garantir a continuidade dos serviços essenciais (Energia, Água, Acesso e Condições Ambientais) sob falhas de conectividade e ataques cibernéticos.

## Integrantes 4ECS
Leticia Naomi Wakai RM99023
Rene Stachetti Damasceno RM98596
Vitor Rodrigues da Silva Oliveira RM558849

## Requisitos de Sistema
* Docker e Docker Compose
* Python 3.10+
* WireGuard (Cliente VPN)

## 1. Subindo a Infraestrutura Base (Arquitetura e Segmentação)
A infraestrutura utiliza o `docker-compose.yml` para orquestrar os contêineres e garantir a segmentação entre dispositivos IoT, Operadores e Serviços Administrativos.

```bash
# Iniciar a Autoridade Certificadora (Step-CA), Broker MQTT e Banco de Dados
docker-compose up -d pki mqtt db