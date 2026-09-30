from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, EmailStr, Field, field_validator

app = FastAPI(title="Mini Blog")

BLOG_POST = [
    {"id": 1, "title": "Hola desde FastAPI",
        "content": "Mi primer post con FastAPI"},
    {"id": 2, "title": "Mi segundo Post con FastAPI",
        "content": "Mi segundo post con FastAPI blablabla"},
    {"id": 3, "title": "Django vs FastAPI",
        "content": "FastAPI es más rápido por x razones",
        "tags": [
            {"name": "Python"},
            {"name": "fastapi"},
            {"name": "Django"}
        ]},
    {"id": 4, "title": "Hola desde FastAPI",
        "content": "Mi primer post con FastAPI"},
    {"id": 5, "title": "Mi segundo Post con FastAPI",
        "content": "Mi segundo post con FastAPI blablabla"},
    {"id": 6, "title": "Django vs FastAPI",
        "content": "FastAPI es más rápido por x razones"},
    {"id": 7, "title": "Hola desde FastAPI",
        "content": "Mi primer post con FastAPI"},
    {"id": 8, "title": "Mi segundo Post con FastAPI",
        "content": "Mi segundo post con FastAPI blablabla"},
    {"id": 9, "title": "Django vs FastAPI",
        "content": "FastAPI es más rápido por x razones"},
    {"id": 10, "title": "Hola desde FastAPI",
        "content": "Mi primer post con FastAPI"},
    {"id": 11, "title": "Mi segundo Post con FastAPI",
        "content": "Mi segundo post con FastAPI blablabla"},
    {"id": 12, "title": "Django vs FastAPI",
        "content": "FastAPI es más rápido por x razones",
        "tags": [
            {"name": "Python"},
            {"name": "fastapi"},
            {"name": "Django"}
        ]},
    {"id": 13, "title": "Hola desde FastAPI",
        "content": "Mi primer post con FastAPI"},
    {"id": 14, "title": "Mi segundo Post con FastAPI",
        "content": "Mi segundo post con FastAPI blablabla"},
    {"id": 15, "title": "Django vs FastAPI",
        "content": "FastAPI es más rápido por x razones",
        "tags": [
            {"name": "Python"},
            {"name": "fastapi"},
            {"name": "Django"}
        ]},
]


# Metodos anidados
class Tag(BaseModel):
    name: str = Field(..., min_length=2, max_length=30, description="names tags")


class Author(BaseModel):
    name: str = None
    email: EmailStr = None


# Modelado de datos con Pydanic
class PostBase(BaseModel):
    title: str
    content: str | None = "No content"
    tags: list[Tag] = Field(default_factory=list)
    author: Author = None


class PostCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Titulo del post (minimo 3 caracteres, max 150)",
        examples=["Mi primer post con FastAPI"],
    )
    content: str | None = Field(
        default="No content",
        min_length=10,
        description="Contenido del post (minimo 10 caracteres)",
        examples=["Este es un contenido valido porque tiene mas de 9 caracteres"],
    )
    tags: list[Tag] = Field(default_factory=list)
    author: Author = None

    @field_validator("title")
    @classmethod
    def not_allowed_title(cls, value: str) -> str:
        forbidden_words = ["porn", "xxx", "spam", "sex"]
        for word in forbidden_words:
            if word in value.lower():
                raise ValueError(f"The title can't content {word}")
        
        return value


class PostUpdate(BaseModel):
    title: str = Field(None, min_length=3, max_length=100)
    content: str | None = None
    tags: list[Tag] = Field(default_factory=list)
    author: Author = None


class PostPublic(PostBase):
    id: int


class PostSummary(BaseModel):
    id: int
    title: str


class PaginatedPost(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[PostPublic]


# METODOS GET
@app.get("/")
def home():
    return {"message": "welcome to mini blog"}


## query params
@app.get("/posts", response_model=PaginatedPost)
def list_posts(
    query: Annotated[
        str | None,
        Query(
            alias="search", max_length=50, description="Search query for blog post title"
        ),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=50, description="Page number (1-50)")] = 10,
    offset: Annotated[
        int, Query(ge=0, description="Items to skip before starting the list")
    ] = 0,
    order_by: Literal["id", "title"] = Query("id", description="Order field"),
    direction: Literal["asc", "desc"] = Query("asc", description="Order direction"),
):
    results = BLOG_POST        
    results = sorted(
        results, key=lambda post: post[order_by], reverse=(direction=="desc")
    )
    items = results[offset: offset + limit]
    if query:
        results = [post for post in results if query.lower() in post["title"].lower()]
        if not len(results):
            raise HTTPException(status_code=404, detail=f"{query} not found")
        else:
            results = sorted(
                results, key=lambda post: post[order_by], reverse=(direction=="desc")
            )
            items = results[offset: offset + limit]
            return PaginatedPost(total=len(results), limit=limit, offset=offset, items=items)  # noqa: E501
        
    return PaginatedPost(total=len(results), limit=limit, offset=offset, items=items) 


## path params
@app.get(
    "/post/{post_id}",
    response_model=PostPublic | PostSummary,
    response_model_exclude_unset=True,
    response_description="Post found",
)
def get_post(
    post_id: int = Path(
        ..., ge=1, title="Post Id", description="Should be greater than 0"
    ),
    include_contet: bool = Query(default=True, description="include or not content"),
):
    for post in BLOG_POST:
        if post["id"] == post_id:
            if include_contet:
                return post
            return {"id": post["id"], "title": post["title"]}

    return HTTPException(status_code=404, details="Post not faound")


# METODOS POST
@app.post(
    "/post",
    response_model=PostPublic,
    response_description="Post created (OK)",
    response_model_exclude_defaults=True,
)
def create_post(post: PostCreate):
    new_id = (BLOG_POST[-1]["id"] + 1) if BLOG_POST else 1
    new_post = {
        "id": new_id,
        "title": post.title,
        "content": post.content,
        "tags": [tag.model_dump() for tag in post.tags],
        "author": post.author.model_dump() if post.author else None,
    }
    BLOG_POST.append(new_post)
    return new_post


# METODO PUT
@app.put(
    "/post/{post_id}",
    response_model=PostPublic,
    response_description="Update post (OK)",
    response_model_exclude_unset=True,
    response_model_exclude_defaults=True,
    response_model_exclude_none=True,
)
def update_post(post_id: int, update_data: PostUpdate):
    for post in BLOG_POST:
        if post["id"] == post_id:
            playload = update_data.model_dump(exclude_unset=True)
            if "title" in playload:
                post["title"] = playload["title"]
            if "content" in playload:
                post["content"] = playload["content"]
            if "tags" in playload:
                post["tags"] = playload["tags"]
            if "author" in playload:
                post["author"] = playload["author"]
            return post

    raise HTTPException(status_code=404, detail="Post not found")


# METODO DELETE
@app.delete("/post/{post_id}", status_code=204, response_description="Post deleted")
def delete_post(post_id: int):
    for index, post in enumerate(BLOG_POST):
        if post["id"] == post_id:
            BLOG_POST.pop(index)
            return
    
    raise HTTPException(status_code=404, detail="Post not found ")
