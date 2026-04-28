from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(
    prefix="/participantes",
    tags=["Participantes"]
)

class AtualizarStatusParticipacao(BaseModel):
    status_gravacao: str 

@router.patch("/{participante_id}/status")
async def atualizar_status(participante_id: str, status: AtualizarStatusParticipacao):
    
    if status.status_gravacao not in ["ja_participei", "ainda_participarei"]:
        raise HTTPException(status_code=400, detail="Status inválido.")

    return {
        "message": "Status atualizado com sucesso!", 
        "participante_id": participante_id,
        "novo_status": status.status_gravacao
    }