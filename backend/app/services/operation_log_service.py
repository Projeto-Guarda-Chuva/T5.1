from app.schemas.operation_log import OperationLogEntry, OperationLogListResponse


class OperationLogService:
    """Orchestrate retrieval and normalization of operation log records."""

    def list_operation_logs(self) -> OperationLogListResponse:
        """
        Fetch logs from the external API, map them to the internal schema,
        and return a normalized response.

        Args:
            None.

        Returns:
            OperationLogListResponse: Normalized list of log entries with total
            count and a descriptive message.

        Raises:
            ProgramadorAtuacaoIntegrationError: Propagated from the service when the
                external API is unreachable or returns a non-200 status.
        """
        from app.services.programador_atuacao_service import ProgramadorAtuacaoService

        raw_events = ProgramadorAtuacaoService().fetch_logs()
        entries = [self._to_entry(event) for event in raw_events]

        return OperationLogListResponse(
            items=entries,
            total=len(entries),
            message=(
                "Logs recuperados com sucesso."
                if entries
                else "Nenhum log encontrado."
            ),
        )

    @staticmethod
    def _to_entry(raw_event: dict) -> OperationLogEntry:
        """
        Convert a single raw external log event to an OperationLogEntry.

        Args:
            raw_event (dict): A single event dict as returned by the external API.

        Returns:
            OperationLogEntry: The normalized internal representation.
        """
        payload: dict = raw_event["payload"]
        parameters: dict = payload["parameters"]

        is_active: bool = payload.get("is_active", False)
        has_capture: bool = (
            parameters.get("video_capture_enabled", False)
            or parameters.get("audio_capture_enabled", False)
        )

        if is_active and has_capture:
            status, status_text = "success", "Concluído"
        else:
            status, status_text = "error", "Inativo ou sem captura"

        name: str = payload.get("name", payload.get("id", ""))
        video: str = "habilitado" if parameters.get("video_capture_enabled") else "desabilitado"
        audio: str = "habilitado" if parameters.get("audio_capture_enabled") else "desabilitado"

        return OperationLogEntry(
            id=payload["id"],
            occurred_at=raw_event["timestamp"],
            duration_seconds=int(parameters["movement_duration_seconds"]),
            participant_email="",
            status=status,
            status_text=status_text,
            description=(
                f"Configuração '{name}' recebida. "
                f"Vídeo {video}, áudio {audio}. "
                f"Velocidade {parameters.get('movement_speed', 0)}, "
                f"duração {parameters.get('movement_duration_seconds', 0)}s."
            ),
        )