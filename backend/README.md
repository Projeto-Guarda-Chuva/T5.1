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

Hoje existe a implementação das histórias:

- `OA-11 (1.2.1) - Visualizar configurações existentes`
- `OA-12 (1.2.2) - Criar nova configuração básica`
- `OA-13 (1.2.3) - Selecionar uma configuração para uso`
- `OA-14 (1.2.4) - Visualizar log da operação`

Arquivos envolvidos:

- `app/routers/configurations.py`
- `app/services/configuration_service.py`
- `app/repositories/configuration_repository.py`
- `app/schemas/configuration.py`
- `app/data/configurations.json`

Rotas disponíveis:

- `GET /configurations`
- `POST /configurations`
- `PATCH /configurations/{configuration_id}/activate`
- `GET /configurations/current`
- `GET /configurations/{configuration_id}`

Aliases de compatibilidade:

- `GET /configuracoes`
- `POST /configuracoes`
- `PATCH /configuracoes/{configuration_id}/ativar`
- `GET /configuracoes/atual`
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

Exemplo de criação:

```json
{
  "name": "Basic Program - New Operation",
  "description": "Configuration for a new operation.",
  "parameters": {
    "movement_speed": 0.7,
    "movement_duration_seconds": 20,
    "video_capture_enabled": true,
    "audio_capture_enabled": false
  }
}
```

Exemplo de seleção para uso:

```json
{
  "configuration": {
    "id": "cfg-002",
    "name": "Basic Program - Silent Operation",
    "description": "Alternative configuration for environments with lower audio capture needs.",
    "is_active": true,
    "created_at": "2026-04-18T11:15:00",
    "updated_at": "2026-05-08T10:15:00",
    "parameters": {
      "movement_speed": 0.6,
      "movement_duration_seconds": 45,
      "video_capture_enabled": true,
      "audio_capture_enabled": false
    }
  },
  "message": "Configuration selected successfully for operation."
}
```

Exemplo de consulta da configuração em uso pela camada inferior:

```json
{
  "configuration": {
    "id": "cfg-002",
    "name": "Basic Program - Silent Operation",
    "description": "Alternative configuration for environments with lower audio capture needs.",
    "is_active": true,
    "created_at": "2026-04-18T11:15:00",
    "updated_at": "2026-05-08T10:15:00",
    "parameters": {
      "movement_speed": 0.6,
      "movement_duration_seconds": 45,
      "video_capture_enabled": true,
      "audio_capture_enabled": false
    }
  },
  "source": "active",
  "has_active_configuration": true,
  "message": "Active configuration retrieved successfully."
}
```

Se nenhuma configuração estiver ativa, `GET /configurations/current` devolve a configuração padrão de fallback.
A regra adotada no backend para esse fallback é usar a configuração mais antiga cadastrada e informar isso no campo `message`.

Se a configuração não existir, a API responde com `404`.
Se faltar campo obrigatório na criação, a API impede o salvamento e responde com erro de validação.

## Histórico da operação

Arquivos envolvidos:

- `app/routers/operation_logs.py`
- `app/services/operation_log_service.py`
- `app/repositories/operation_log_repository.py`
- `app/schemas/operation_log.py`
- `app/data/operation_logs.json`

Rotas disponíveis:

- `GET /operation-logs`

Aliases de compatibilidade:

- `GET /logs-operacao`

Exemplo de resposta:

```json
{
  "items": [
    {
      "id": "SESS-1042",
      "occurred_at": "2026-05-01T14:30:00",
      "duration_seconds": 312,
      "participant_email": "usuario1@exemplo.com",
      "status": "success",
      "status_text": "Concluído",
      "description": "Sessão finalizada com gravação e execução normal da operação."
    }
  ],
  "total": 1,
  "message": "Operation log records retrieved successfully."
}
```

Caso não existam registros armazenados em `app/data/operation_logs.json`, a API responde com lista vazia e a mensagem `No operation log records found.`.

## Envio do vídeo do dia por e-mail

Arquivos envolvidos:

- `app/routers/participantes.py`
- `app/services/participant_video_email_service.py`
- `app/services/video_email_sender.py`
- `app/repositories/participant_repository.py`
- `app/repositories/participant_video_repository.py`
- `app/repositories/video_file_repository.py`
- `app/repositories/video_email_dispatch_repository.py`
- `app/repositories/email_outbox_repository.py`
- `app/startup_seed.py`
- `app/schemas/participant_video_email.py`

Rotas disponíveis:

- `POST /participantes/{participante_id}/videos/{video_id}/arquivo`
- `POST /participantes/{participante_id}/video-do-dia/email`

Alias de compatibilidade:

- `POST /participantes/{participante_id}/videos/enviar-email`

Regra implementada:

1. o backend localiza o participante pelo `participante_id`
2. o arquivo do vídeo pode ser salvo explicitamente no Mongo usando `POST /participantes/{participante_id}/videos/{video_id}/arquivo`
3. o upload grava o binário no MongoDB GridFS e atualiza o `file_id` no documento correspondente em `participant_videos`
4. no envio por e-mail, o backend usa o e-mail cadastrado no participante
5. procura o vídeo da data informada em `reference_date`
6. se houver vídeo disponível, recupera o arquivo salvo no MongoDB GridFS
7. se o arquivo existir, envia o vídeo como anexo por SMTP quando configurado
8. se SMTP não estiver configurado, registra o e-mail na coleção Mongo `email_outbox`
9. em caso de sucesso, grava uma auditoria na coleção Mongo `video_email_dispatch_logs`
10. participantes e vídeos são lidos das coleções Mongo `participants` e `participant_videos`
11. o binário do vídeo fica no bucket GridFS `videos`

Bootstrap local:

- o backend não semeia mais participantes, vídeos ou logs a partir de arquivos JSON
- no startup, `app/startup_seed.py` apenas garante os índices Mongo necessários
- o backend não vincula nenhum `.mp4` de demonstração automaticamente
- o envio por e-mail só acontece quando o vídeo correto do participante já tiver sido salvo no MongoDB GridFS por upload explícito

Fluxo recomendado sem frontend:

1. subir o backend
2. enviar o `.mp4` para um vídeo específico com `POST /participantes/{participante_id}/videos/{video_id}/arquivo`
3. disparar `POST /participantes/{participante_id}/video-do-dia/email`

Exemplo de upload do arquivo:

```bash
curl -X POST "http://127.0.0.1:8000/participantes/part-001/videos/vid-001/arquivo" \
  -F "video=@/caminho/para/video.mp4"
```

Resposta de exemplo do upload:

```json
{
  "participant_id": "part-001",
  "video": {
    "id": "vid-001",
    "title": "Vídeo da participação - 14/05/2026",
    "recorded_at": "2026-05-14T14:30:00",
    "filename": "video.mp4",
    "content_type": "video/mp4",
    "size_bytes": 13294212
  },
  "message": "Arquivo do vídeo salvo no MongoDB com sucesso."
}
```

Payload de exemplo:

```json
{
  "reference_date": "2026-05-14"
}
```

O campo `reference_date` é opcional. Quando ele não for enviado, o backend usa a data atual do servidor.

Exemplo de resposta:

```json
{
  "dispatch_id": "dispatch-001",
  "sent_at": "2026-05-14T18:05:00",
  "participant_id": "part-001",
  "participant_email": "comvideos@teste.com",
  "reference_date": "2026-05-14",
  "delivery_mode": "outbox",
  "video": {
    "id": "vid-001",
    "title": "Vídeo da participação - 14/05/2026",
    "recorded_at": "2026-05-14T14:30:00",
    "filename": "video.mp4",
    "content_type": "video/mp4",
    "size_bytes": 13294212
  },
  "message": "SMTP não configurado. O envio do vídeo anexado foi registrado na outbox local para validação do fluxo."
}
```

Respostas de erro esperadas:

- `404` quando o participante não existir
- `404` quando não houver vídeo para a data pedida
- `409` quando houver vídeo do dia, mas ele ainda não estiver disponível para envio
- `409` quando o vídeo existir, mas o arquivo ainda não estiver salvo no banco de dados
- `409` quando existir um `file_id`, mas o arquivo salvo no GridFS não estiver vinculado ao mesmo participante e vídeo
- `400` quando o participante não tiver e-mail válido cadastrado
- `502` quando o SMTP estiver configurado, mas o envio falhar

Variáveis opcionais para envio SMTP real:

```text
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_USE_STARTTLS=true
SMTP_TIMEOUT_SECONDS=120
VIDEO_GRIDFS_BUCKET_NAME=videos
```

Compatibilidade com configuração já usada pelo projeto:

```text
MAIL_SERVER=
MAIL_PORT=
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_STARTTLS=true
```

Se `MAIL_*` for usado sem `MAIL_SERVER` ou `SMTP_HOST`, o backend assume `smtp.gmail.com` quando o remetente for uma conta `@gmail.com`.

## Integração local com o frontend

Para o frontend consumir essa API localmente, basta apontar a base URL para:

```text
http://127.0.0.1:8000
```

O backend já aceita chamadas do frontend rodando localmente nas portas mais comuns do Vite.
