from fastapi import FastAPI, Depends, HTTPException, Query, Path, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn

app = FastAPI(title="Production REST API", version="1.0.0")

# --- Models (Pydantic for validation) ---
class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100, description="Title of the article")
    content: str = Field(..., min_length=10, description="Body of the article")

class ArticleResponse(ArticleCreate):
    id: int
    author: str

# Mock Database
db = {}
next_id = 1

# --- Dependencies (Middlewares / Authentication) ---
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Real-world authentication dependency.
    FastAPI will automatically inject this, read the Authorization header, and validate it.
    """
    token = credentials.credentials
    if token != "secret-production-token":
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    # Return the simulated user ID
    return "admin_99"

# --- Routes / Handlers ---

@app.post("/api/v1/articles", response_model=ArticleResponse, status_code=201)
async def create_article(
    # Body binding happens automatically via Pydantic model
    article: ArticleCreate = Body(...),
    # Dependency injection for auth
    user_id: str = Depends(verify_token) 
):
    global next_id
    new_article = ArticleResponse(
        id=next_id,
        title=article.title,
        content=article.content,
        author=user_id
    )
    db[next_id] = new_article
    next_id += 1
    return new_article


@app.get("/api/v1/articles", response_model=List[ArticleResponse])
async def get_articles(
    # Query parameters with defaults and validation
    limit: int = Query(10, ge=1, le=100, description="Max number of articles to return"),
    sort: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    user_id: str = Depends(verify_token)
):
    articles = list(db.values())
    
    if sort == "desc":
        articles.reverse()
        
    return articles[:limit]


@app.get("/api/v1/articles/{article_id}", response_model=ArticleResponse)
async def get_article_by_id(
    # Path parameter validation
    article_id: int = Path(..., gt=0, description="The ID of the article"),
    user_id: str = Depends(verify_token)
):
    if article_id not in db:
        raise HTTPException(status_code=404, detail="Article not found")
    return db[article_id]


@app.put("/api/v1/articles/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int = Path(...),
    article_update: ArticleCreate = Body(...),
    user_id: str = Depends(verify_token)
):
    if article_id not in db:
        raise HTTPException(status_code=404, detail="Article not found")
        
    updated_article = ArticleResponse(
        id=article_id,
        title=article_update.title,
        content=article_update.content,
        author=user_id
    )
    db[article_id] = updated_article
    return updated_article


@app.delete("/api/v1/articles/{article_id}", status_code=204)
async def delete_article(
    article_id: int = Path(...),
    user_id: str = Depends(verify_token)
):
    if article_id not in db:
        raise HTTPException(status_code=404, detail="Article not found")
    del db[article_id]
    return # 204 requires no body

if __name__ == "__main__":
    print("Run API with: uvicorn comprehensive_production_api:app --reload")
    # uvicorn.run(app, host="0.0.0.0", port=8000)
