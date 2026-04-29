# Backend T5.1

Este diretório contém o backend da aplicação `T5.1`, implementado em `Python` com `FastAPI`.

## Estrutura

```text
backend/
├── app/
│   ├── config.py
│   ├── database.py
│   ├── data/
│   ├── repositories/
│   ├── routers/
│   ├── schemas/
│   └── services/
├── main.py
├── requirements.txt
└── README.md
```

## Papel de cada camada

- `routers`: define as rotas da API, como `GET`, `POST`, `PATCH`
- `services`: concentra a regra de negócio
- `repositories`: faz o acesso aos dados
- `schemas`: define o formato de entrada e saída da API
- `data`: pode guardar dados locais provisórios enquanto a integração final não está pronta

## Fluxo padrão

Quando o frontend chama uma rota:

1. o `router` recebe a requisição
2. o `router` chama o `service`
3. o `service` aplica a regra de negócio
4. o `service` chama o `repository`, se precisar de dados
5. o backend devolve a resposta em JSON

## Como o frontend usa o backend

O frontend se comunica com este backend por código, chamando as rotas da API.

Exemplo:

```ts
api.get("/configurations");
```

Isso faz o FastAPI executar a função Python ligada à rota `/configurations`.

Para integração local via navegador, o backend já está configurado com CORS para portas comuns do Vite, como `5173` e `5174`.

## Padrão para novas histórias

Ao implementar uma nova história no backend, o ideal é seguir este padrão:

1. criar ou atualizar um arquivo em `app/routers`
2. criar ou atualizar os `schemas`
3. criar ou atualizar a lógica em `app/services`
4. criar ou atualizar o acesso a dados em `app/repositories`
5. registrar a rota no `main.py`, se necessário
6. documentar no README da pasta, se a funcionalidade gerar contrato para o frontend

## Exemplo atual

Hoje existe a implementação da história `OA-11 (1.2.1) - Visualizar configurações existentes`.

Arquivos envolvidos:

- `app/routers/configurations.py`
- `app/services/configuration_service.py`
- `app/repositories/configuration_repository.py`
- `app/schemas/configuration.py`
- `app/data/configurations.json`

Rotas disponíveis:

- `GET /configurations`
- `GET /configurations/{configuration_id}`

Aliases de compatibilidade:

- `GET /configuracoes`
- `GET /configuracoes/{configuration_id}`

Exemplo de resposta da listagem:

```json
{
  "items": [
    {
      "id": "cfg-001",
      "name": "Basic Program - Default Display",
      "description": "Default configuration for regular robot operation during short exhibitions.",
      "is_active": true,
      "created_at": "2026-04-17T09:00:00",
      "updated_at": "2026-04-22T14:30:00"
    }
  ],
  "total": 1,
  "message": "Configurations retrieved successfully."
}
```

Exemplo de resposta do detalhe:

```json
{
  "id": "cfg-001",
  "name": "Basic Program - Default Display",
  "description": "Default configuration for regular robot operation during short exhibitions.",
  "is_active": true,
  "created_at": "2026-04-17T09:00:00",
  "updated_at": "2026-04-22T14:30:00",
  "parameters": {
    "movement_speed": 0.8,
    "movement_duration_seconds": 30,
    "video_capture_enabled": true,
    "audio_capture_enabled": true
  }
}
```

Se a configuração não existir, a API responde com `404`.

## Integração local com o frontend

Para o frontend consumir essa API localmente, basta apontar a base URL para:

```text
http://127.0.0.1:8000
```

O backend já aceita chamadas do frontend rodando localmente nas portas mais comuns do Vite.
