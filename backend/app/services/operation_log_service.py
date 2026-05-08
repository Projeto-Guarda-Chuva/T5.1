from datetime import datetime

from app.schemas.operation_log import OperationLogEntry, OperationLogListResponse


class OperationLogService:
    """Apply business rules for operation log read operations."""

    def __init__(self, repository) -> None:
        self._repository = repository

    def list_operation_logs(self) -> OperationLogListResponse:
        """
        Return all stored operation logs formatted for the API response model.

        Args:
            None.

        Returns:
            OperationLogListResponse: The API response containing operation log entries.
        """
        operation_logs = self._repository.list_all()
        sorted_logs = sorted(
            operation_logs,
            key=lambda log: self._parse_sortable_datetime(log.get("occurred_at")),
            reverse=True,
        )
        items = [OperationLogEntry(**log) for log in sorted_logs]

        if not items:
            return OperationLogListResponse(
                items=[],
                total=0,
                message="No operation log records found.",
            )

        return OperationLogListResponse(
            items=items,
            total=len(items),
            message="Operation log records retrieved successfully.",
        )

    def _parse_sortable_datetime(self, value: str | None) -> datetime:
        """
        Convert an ISO timestamp to a sortable datetime value.

        Args:
            value (str | None): ISO timestamp string.

        Returns:
            datetime: Parsed datetime or datetime.min when the input is invalid.
        """
        if not value:
            return datetime.min

        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.min
