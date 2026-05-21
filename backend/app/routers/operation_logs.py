from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.schemas.operation_log import OperationLogListResponse
from app.services.operation_log_service import OperationLogService
from app.services.programador_atuacao_service import ProgramadorAtuacaoIntegrationError

router = APIRouter(tags=["Operation Logs"], dependencies=[Depends(get_current_user)])

operation_log_service = OperationLogService()


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
    Return all operation log records fetched from the external API.

    Args:
        None.

    Returns:
        OperationLogListResponse: A list of normalized operation log records,
        the total count, and a message describing the result.

    Raises:
        HTTPException: With the external API's status code when it is
            unreachable or returns an error response.
    """
    try:
        return operation_log_service.list_operation_logs()
    except ProgramadorAtuacaoIntegrationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc