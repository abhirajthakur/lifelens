from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.db import DBSession
from app.core.deps import CurrentUser
from app.services.query_processor import process_query

router = APIRouter(prefix="/api/query", tags=["query"])


class QueryRequest(BaseModel):
    query: str = Field(..., description="User query")


@router.post("")
async def query_media(request: QueryRequest, db: DBSession, current_user: CurrentUser):
    try:
        result = process_query(db=db, query=request.query, user_id=current_user.id)

        if result.get("error"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return {
            "query": request.query,
            "response": result.get("response"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
