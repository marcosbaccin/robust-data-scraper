# 🕸️ Robust Data Scraper

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue?logo=docker)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-blue?logo=postgresql)
![Status](https://img.shields.io/badge/Status-Completed-success)

Pipeline de Engenharia de Dados resiliente para extração, validação e armazenamento de dados de e-commerce (Kabum), focado em estabilidade e qualidade de dados.

## 📋 Sobre o Projeto

Este projeto resolve o problema de extração de dados em sites dinâmicos (SPAs) que utilizam carregamento tardio (Lazy Loading) e proteções anti-bot. A arquitetura foi desenhada para ser agnóstica ao ambiente, rodando 100% em containers.

**Principais Diferenciais:**
- **Resiliência:** Implementação de *Retry Pattern* para aguardar dependências (Selenium Grid).
- **Qualidade:** Validação de esquema de dados em tempo de execução com **Pandera** (Fail Fast).
- **Infraestrutura:** Orquestração completa via Docker Compose (Scraper + Selenium Hub + Postgres).

## 🏗️ Arquitetura

O projeto segue o padrão de microsserviços containerizados:

1.  **Selenium Hub (Chrome):** Navegador headless isolado.
2.  **Scraper (Python):** Aplicação que orquestra a navegação e extração.
3.  **PostgreSQL:** Banco de dados para persistência dos dados estruturados.

## 🚀 Como Rodar

### Pré-requisitos
- Docker e Docker Compose instalados.

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/SEU_USUARIO/robust-data-scraper.git](https://github.com/SEU_USUARIO/robust-data-scraper.git)
   cd robust-data-scraper

2. **Inicie o Pipeline:**
    ```bash
    docker-compose up --build
    ```
    *O script irá aguardar o banco de dados e o navegador estarem prontos antes de iniciar.*

3. **Verifique os Dados: Acesse o container do banco para validar a ingestão sem precisar instalar nada extra:**
   ```bash
   docker exec -it robust-data-scraper-db_postgres-1 psql -U admin -d kabum_db -c "SELECT * FROM precos_placas_video;"

## 🛠️ Tecnologias

- **Linguagem:** Python 3.11
- **Web Driver:** Selenium WebDriver
- **Validação:** Pandera & Pydantic
- **Banco de Dados:** PostgreSQL 15
- **ORM:** SQLAlchemy