# Datadog Agent + LiteLLM + Agent App

A Docker Compose setup that runs a LiteLLM proxy, a multi-agent Python chat app, and a Datadog Agent, with APM tracing, LLM observability, and log collection wired together out of the box.

## Prerequisites

- Docker and Docker Compose installed
- A Datadog API key
- API keys for whichever LLM providers you plan to use

## Setup

**1. Copy the example env file and fill in your secrets:**

```bash
cp .env.example .env
```

Open `.env` and set at minimum:

| Variable | Description |
|---|---|
| `DD_API_KEY` | Your Datadog API key |
| `DD_APP_KEY` | Your Datadog application key (required for LiteLLM native callbacks) |
| `DD_SITE` | Your Datadog site (default: `datadoghq.com`) |
| `LITELLM_MASTER_KEY` | Master key for the LiteLLM proxy (any string, e.g. `sk-my-key`) |
| `OPENAI_API_KEY` | OpenAI API key (if using OpenAI models) |

Other supported sites: `datadoghq.eu`, `us3.datadoghq.com`, `us5.datadoghq.com`, `ap1.datadoghq.com`.

**2. (Optional) Edit `litellm_config.yaml`** to add or remove models.

**3. (Optional) Edit `datadog.yaml`** to adjust Datadog Agent configuration. The file is mounted at `/etc/datadog-agent/datadog.yaml` inside the agent container. `DD_API_KEY` and `DD_SITE` are injected at runtime from your `.env` and do not need to be hardcoded.

## Starting the stack

```bash
docker compose --env-file .env up -d
```

Check that all containers are running:

```bash
docker compose ps
```

View logs:

```bash
# All services
docker compose logs -f

# Individual service
docker compose logs -f agent-app
docker compose logs -f litellm
docker compose logs -f datadog-agent
```

## Chat UI

The agent app serves a browser-based chat UI powered by [Chainlit](https://chainlit.io). Once the stack is up, open:

```
http://localhost:8000
```

The app uses three agents wired together with handoffs:

| Agent | Responsibility | Tools |
|---|---|---|
| Router Agent | Reads the user message and hands off to the right specialist | (none, routing only) |
| Weather Agent | Answers weather and forecast questions | `get_weather`, `get_weather_forecast` |
| Generic Agent | Handles time lookups, math, and general questions | `get_current_time`, `calculate` |

## Using the LiteLLM proxy

The proxy listens on `http://localhost:4000`. Send requests using the OpenAI-compatible API, authenticating with your `LITELLM_MASTER_KEY`:

```bash
curl http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-my-key" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

Available model names are defined in `litellm_config.yaml` under `model_list`.

## Datadog observability

| Signal | Source | How |
|---|---|---|
| APM traces | `agent-app` | `ddtrace` auto-instrumentation via `ddtrace-run`, service `agent-app` |
| LLM Observability | `agent-app` | `DD_LLMOBS_ENABLED=1`, ML app `agent-app` |
| LLM Observability | `litellm` | Native Datadog callback (`datadog_llm_observability`), sent directly to cloud API |
| Metrics | `litellm` | Native Datadog callback (`datadog_metrics`) via DogStatsD on port `8125` |
| Cost tracking | `litellm` | Native Datadog callback (`datadog_cost_management`), sent directly to cloud API |
| Logs | All containers | Collected by agent automatically; `source:python service:agent-app`, `source:litellm service:litellm` |

## Stopping the stack

```bash
docker compose down
```
# datadog-litellm
