# MovieChoice — Backend (Flask)

Backend em Python/Flask para o app Flutter [movie_choice](https://github.com/isagusmao97/movie_choice). Implementa salas de votação de filmes: criar sala, entrar com código, sugerir filmes e votar.

## Stack

| Camada | Escolha | Justificativa |
|---|---|---|
| Framework web | **Flask 3.0** | Requisito da disciplina. Padrão para APIs Python pequenas/médias. |
| ORM | **Flask-SQLAlchemy** | Padrão do ecossistema Flask. [Documentação oficial](https://flask.palletsprojects.com/en/stable/patterns/sqlalchemy/) recomenda. |
| Banco | **SQLite** | Zero configuração; basta um arquivo. Trocar para Postgres em produção é mudar uma variável de ambiente. |
| CORS | **Flask-CORS** | Sem isto, o Flutter Web (em outra porta) não consegue chamar a API por bloqueio do navegador. |
| Config | **python-dotenv** | Carrega `.env` automaticamente. Boa prática (12-Factor App). |

## Estrutura

```
movie_choice_backend/
├── app.py              # Application factory + entrypoint
├── models.py           # Modelos SQLAlchemy (Sala, Membro, Filme, Voto)
├── routes.py           # Blueprint da API (/api/*)
├── requirements.txt
├── .env.example
├── .gitignore
└── instance/           # Banco SQLite (gerado em runtime, gitignored)
    └── moviechoice.db
```

## Como rodar

### 1. Pré-requisitos

- Python 3.10+

### 2. Setup

```bash
# Clone (ou copie esta pasta para dentro do seu projeto)
cd movie_choice_backend

# Crie um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate          # Linux/Mac
# venv\Scripts\activate           # Windows PowerShell

# Instale as dependências
pip install -r requirements.txt

# Configure o ambiente
cp .env.example .env
# (edite o .env se quiser. Para dev local funciona como está.)

# para rodar o back-end utilize o comando abaixo antes de rodar o seed
python app.py

# para criar o catálogo de filmes com as informações dos filmes e as capas
# em um segundo terminal rode o comando
python seed_catalogos.py

# se caso for alterado algum dado dentro do json ou no arquivo seed_catalogo.py será preciso apagar os dados do moviechoice.db para gerar um novo com os dados atualizados, para isso o comando abaixo é necessário

# após a exclusão será necessário criar o banco novamente com os comandos anteriores
del instance/moviechoice.db
```

### 3. Rodar

```bash
python app.py
```

A API sobe em `http://localhost:5000`. O banco SQLite é criado automaticamente em `instance/moviechoice.db` na primeira execução.

Teste rápido:
```bash
curl http://localhost:5000/api/health
# {"status": "ok"}
```

## Endpoints

Todos os endpoints retornam JSON. Erros seguem o formato `{"erro": "mensagem"}`.

### `GET /api/health`
Health check. Retorna `{"status": "ok"}`.

### `POST /api/salas` — Criar sala
**Body:**
```json
{
  "nome": "Sessão da turma",
  "expiracao": "24h",
  "tipo_sessao": "Streaming",
  "criador_nome": "Phelipe"
}
```
- `expiracao`: `"24h"`, `"48h"` ou `"72h"`
- `tipo_sessao`: `"Cinema"` ou `"Streaming"`
- `criador_nome`: **opcional**. Se enviado, já cria o usuário como primeiro membro (admin) e retorna seu `membro_atual.id` para você guardar no cliente.

**Resposta 201:**
```json
{
  "id": "uuid-da-sala",
  "codigo": "ABC123",
  "nome": "Sessão da turma",
  "tipo_sessao": "Streaming",
  "criada_em": "2026-...",
  "expira_em": "2026-...",
  "expirada": false,
  "criador_id": "uuid-do-membro",
  "membros": [...],
  "filmes": [],
  "membro_atual": { "id": "uuid", "nome": "Phelipe" }
}
```

### `GET /api/salas/<codigo>` — Buscar sala
Retorna a sala com `membros` e `filmes` (cada filme com `total_votos`). 404 se não existir.

### `POST /api/salas/<codigo>/entrar` — Entrar na sala
**Body:** `{"nome": "Maria"}`

**Resposta 201:**
```json
{
  "membro_atual": { "id": "uuid", "nome": "Maria", "entrou_em": "..." },
  "sala": { ... estado completo da sala ... }
}
```

Erros: `404` (sala inexistente), `410` (expirada).

### `POST /api/salas/<codigo>/filmes` — Sugerir filme
**Body:** `{"titulo": "O Senhor dos Anéis", "membro_id": "uuid-do-membro"}`

Erros: `403` se o `membro_id` não pertencer à sala, `410` se sala expirou.

### `POST /api/filmes/<filme_id>/votar` — Votar
**Body:** `{"membro_id": "uuid-do-membro"}`

Resposta: `{"ok": true, "total_votos": N}`.
Erros: `403` (membro não é da sala), `409` (já votou neste filme), `410` (sala expirou).

