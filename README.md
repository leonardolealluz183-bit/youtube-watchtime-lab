# YouTube Watchtime Lab

Projeto acadêmico para simular e analisar retenção de audiência em vídeos incorporados com a YouTube IFrame Player API.

## Tecnologias

Python 3.12, FastAPI, SQLAlchemy, SQLite, HTML/CSS/JavaScript sem framework, Chart.js, Playwright e Pytest.

## Instalação

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

## Execução

```bash
uvicorn app.main:app --reload
```

Acesse `http://127.0.0.1:8000` para iniciar sessões e `http://127.0.0.1:8000/dashboard` para ver métricas.

## Simulador local

Com a aplicação em execução:

```bash
python simulator/run_simulation.py --base-url http://127.0.0.1:8000
```

O simulador usa somente a aplicação local e cria perfis engajado, casual, pula trechos e pausa frequentemente.

## Testes

```bash
pytest
```

## Decisões técnicas

- Sessões usam UUID.
- Eventos são validados com Pydantic.
- O watch time efetivo é calculado pela união dos intervalos assistidos, evitando duplicidade quando o usuário retrocede.
- Tempo decorrido da sessão é mantido separadamente pelos timestamps; as métricas priorizam tempo efetivamente assistido.
- SQLite é usado por padrão via `DATABASE_URL`.

## Limitações conhecidas

- A duração real do vídeo pode chegar após o carregamento do player; no MVP ela pode ser aproximada pelo cliente ou simulador.
- Testes automatizados não dependem do YouTube externo.
- A detecção de seek no player real é simplificada e inferida por eventos/posições periódicas.
