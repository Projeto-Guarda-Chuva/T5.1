from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.repositories.operation_log_repository import OperationLogRepository
from app.schemas.operation_log import OperationLogListResponse
from app.services.operation_log_service import OperationLogService

router = APIRouter(tags=["Operation Logs"], dependencies=[Depends(get_current_user)])

operation_log_service = OperationLogService(OperationLogRepository())


@router.get(
    "/operation-logs",
    response_model=OperationLogListResponse,
)
@router.get(
    "/logs-operacao",
    response_model=OperationLogListResponse,
    include_in_schema=False,
)
async def list_operation_logs() -> OperationLogListResponse:
    """
    Return all stored operation log records available to the application.

    Args:
        None.

    Returns:
        OperationLogListResponse: A list of operation log records, the total count,
        and a message describing the result.
    """
    return operation_log_service.list_operation_logs()
