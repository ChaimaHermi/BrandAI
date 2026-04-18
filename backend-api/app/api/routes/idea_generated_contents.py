# Routes : historique des contenus générés (posts sociaux) par idée.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.generated_content import (
    GeneratedContentCreate,
    GeneratedContentListOut,
    GeneratedContentOut,
    GeneratedContentPatch,
)
import app.services.generated_content_service as gc_svc

router = APIRouter(prefix="/ideas", tags=["Contenu généré"])


@router.post(
    "/{idea_id}/generated-contents",
    response_model=GeneratedContentOut,
    status_code=201,
    summary="Enregistrer un contenu généré (traçabilité)",
)
def create_generated_content(
    idea_id: int,
    body: GeneratedContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = gc_svc.create_generated_content(
        db,
        idea_id=idea_id,
        user_id=current_user.id,
        data=body,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Idée introuvable")
    return row


@router.get(
    "/{idea_id}/generated-contents",
    response_model=GeneratedContentListOut,
    summary="Lister les contenus générés pour une idée",
)
def list_generated_contents(
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = gc_svc.list_generated_contents(
        db, idea_id=idea_id, user_id=current_user.id
    )
    if rows is None:
        raise HTTPException(status_code=404, detail="Idée introuvable")
    out = [GeneratedContentOut.model_validate(r) for r in rows]
    return GeneratedContentListOut(items=out, total=len(out))


@router.get(
    "/{idea_id}/generated-contents/count",
    summary="Nombre de contenus générés (aperçu dashboard)",
)
def count_generated_contents(
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    n = gc_svc.count_generated_contents(
        db, idea_id=idea_id, user_id=current_user.id
    )
    if n is None:
        raise HTTPException(status_code=404, detail="Idée introuvable")
    return {"idea_id": idea_id, "count": n}


@router.patch(
    "/{idea_id}/generated-contents/{content_id}",
    response_model=GeneratedContentOut,
    summary="Mettre à jour le statut (publié / échec)",
)
def patch_generated_content(
    idea_id: int,
    content_id: int,
    body: GeneratedContentPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = gc_svc.patch_generated_content(
        db,
        idea_id=idea_id,
        content_id=content_id,
        user_id=current_user.id,
        patch=body,
    )
    if not row:
        raise HTTPException(
            status_code=404,
            detail="Idée ou contenu introuvable",
        )
    return row
