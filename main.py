import os
from math import ceil
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blog.db")
print("Connect to: ", DATABASE_URL)

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=True, future=True, **engine_kwargs)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, class_=Session)

class Base(DeclarativeBase):
    ...


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(title="Mini Blog")

BLOG_POST = [
    {"id": 1, "title": "Hola desde FastAPI", "content": "Mi primer post con FastAPI"},
    {
        "id": 2,
        "title": "Mi segundo Post con FastAPI",
        "content": "Mi segundo post con FastAPI blablabla",
    },
    {
        "id": 3,
        "title": "Django vs FastAPI",
        "content": "FastAPI es más rápido por x razones",
        "tags": [{"name": "Python"}, {"name": "fastapi"}, {"name": "Django"}],
    },
    {"id": 4, "title": "Hola desde FastAPI", "content": "Mi primer post con FastAPI"},
    {
        "id": 5,
        "title": "Mi segundo Post con FastAPI",
        "content": "Mi segundo post con FastAPI blablabla",
        "tags": [{"name": "Python"}, {"name": "string"}, {"name": "Go"}],
    },
    {
        "id": 6,
        "title": "Django vs FastAPI",
        "content": "FastAPI es más rápido por x razones",
    },
    {
        "id": 7,
        "title": "Hola desde FastAPI",
        "content": "Mi primer post con FastAPI",
        "tags": [{"name": "Python"}, {"name": "backend"}, {"name": "js"}],
    },
    {
        "id": 8,
        "title": "Mi segundo Post con FastAPI",
        "content": "Mi segundo post con FastAPI blablabla",
    },
    {
        "id": 9,
        "title": "Django vs FastAPI",
        "content": "FastAPI es más rápido por x razones",
    },
    {"id": 10, "title": "Hola desde FastAPI", "content": "Mi primer post con FastAPI"},
    {
        "id": 11,
        "title": "Mi segundo Post con FastAPI",
        "content": "Mi segundo post con FastAPI blablabla",
    },
    {
        "id": 12,
        "title": "Django vs FastAPI",
        "content": "FastAPI es más rápido por x razones",
        "tags": [{"name": "Python"}, {"name": "fastapi"}, {"name": "Django"}],
    },
    {"id": 13, "title": "Hola desde FastAPI", "content": "Mi primer post con FastAPI"},
    {
        "id": 14,
        "title": "Mi segundo Post con FastAPI",
        "content": "Mi segundo post con FastAPI blablabla",
    },
    {
        "id": 15,
        "title": "Django vs FastAPI",
        "content": "FastAPI es más rápido por x razones",
        "tags": [{"name": "Python"}, {"name": "fastapi"}, {"name": "Django"}],
    },
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
    page: int
    per_page: int
    total: int
    total_pages: int
    has_prev: bool
    has_next: bool
    order_by: Literal["id", "title"]
    direction: Literal["asc", "desc"]
    search: str | None = None
    items: list[PostPublic]


# METODOS GET
@app.get("/")
def home():
    return {"message": "welcome to mini blog"}


## query params
@app.get("/posts", response_model=PaginatedPost)
def list_posts(
    text: Annotated[
        str | None,
        Query(
            alias="text",
            max_length=50,
            description="Search query for blog post title",
            deprecated=True,
        ),
    ] = None,
    query: Annotated[
        str | None,
        Query(
            alias="search",
            max_length=50,
            description="Search query for blog post title",
        ),
    ] = None,
    per_page: Annotated[
        int, Query(ge=1, le=50, description="Number of items per page (1-50)")
    ] = 10,
    page: Annotated[int, Query(ge=1, description="Page Number (>=1)")] = 1,
    order_by: Literal["id", "title"] = Query("id", description="Order field"),
    direction: Literal["asc", "desc"] = Query("asc", description="Order direction"),
):
    results = BLOG_POST

    # query= query or text # solo para probar deprecated parameter
    if query:
        results = [post for post in results if query.lower() in post["title"].lower()]

    total = len(results)
    total_pages = ceil(total / per_page) if total > 0 else 0
    if total_pages == 0:
        current_page = 1
    else:
        current_page = min(page, total_pages)

    results = sorted(
        results, key=lambda post: post[order_by], reverse=(direction == "desc")
    )
    if total_pages == 0:
        items = []
    else:
        start = (current_page - 1) * per_page
        items = results[start : start + per_page]

    has_prev = current_page > 1
    has_next = current_page < total_pages if total_pages > 0 else False

    return PaginatedPost(
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        order_by=order_by,
        direction=direction,
        search=query,
        items=items,
    )


@app.get("/post/by-tags", response_model=list[PostPublic])
def filter_by_tags(
    tags: Annotated[
        list[str],
        Query(
            ...,
            min_length=1,
            description="One or more tags. Example: ?tags=python&tags=fastapi",
        ),
    ],
):
    tags_lower = [tag.lower() for tag in tags]

    return [
        post
        for post in BLOG_POST
        if any(tag["name"].lower() in tags_lower for tag in post.get("tags", []))
    ]


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
