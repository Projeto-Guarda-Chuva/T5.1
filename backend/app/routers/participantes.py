from datetime import datetime
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

    # TODO: Integração com MongoDB

    return {
        "message": "Status atualizado com sucesso!", 
        "participante_id": participante_id,
        "novo_status": status.status_gravacao
    }

class AceiteTermo(BaseModel):
    aceitou: bool
    versao_termo: str

@router.patch("/{participante_id}/aceite-termo")
async def registrar_aceite_termo(participante_id: str, aceite: AceiteTermo):
    if not aceite.aceitou:
        raise HTTPException(
            status_code=400, 
            detail="O participante deve aceitar o termo para prosseguir."
        )

    data_hora_atual = datetime.utcnow().isoformat()
    registro_auditoria = {
        "termo_aceite": {
            "aceitou": aceite.aceitou,
            "data_hora_aceite": data_hora_atual,
            "versao_termo": aceite.versao_termo
        }
    }

    # TODO: Integração com MongoDB

    return {
        "message": "Aceite do termo registrado com sucesso!",
        "participante_id": participante_id,
        "auditoria": registro_auditoria["termo_aceite"]
    }