from fastapi import APIRouter, Depends

from kajet_turbo.api.schemas import TagsResponse
from kajet_turbo.api.schemas.errors import ErrorResponse
from kajet_turbo.dependencies import (
    CurrentUser,
    get_note_tag_service,
    get_required_user,
    resolve_workspace_target,
)
from kajet_turbo.services.notes import NoteTagService
from kajet_turbo.services.targets import WorkspaceTarget

router = APIRouter(
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
    }
)


@router.get("/api/workspaces/{name}/tags", response_model=TagsResponse)
def api_list_tags(
    name: str,
    user: CurrentUser = Depends(get_required_user),
    workspace: WorkspaceTarget = Depends(resolve_workspace_target),
    tag_service: NoteTagService = Depends(get_note_tag_service),
) -> TagsResponse:
    return TagsResponse(tags=tag_service.tag_tree(name, owner_id=user.id))
