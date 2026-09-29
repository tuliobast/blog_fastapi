from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="Mini Blog")

BLOG_POST = [
    {
        "id": 1, 
        "title": "First Post", 
        "content": "This is the first post."
    },
    {
        "id": 2, 
        "title": "Second Post", 
        "content": "This is the second post."
    },
    {
        "id": 3,
        "title": "Django vs FastAPI",
        "content": "FastAPI es mas rapido que Django.",
    },
]


# Modelado de datos con Pydanic
class PostBase(BaseModel):
    title: str
    content: str | None = "Content disable"


class PostCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Titulo del post (minimo 3 caracteres, max 150)",
        examples=["Mi primer post con FastAPI"],
    )
    content: str | None = Field(
        default="Contenido no disponible",
        min_length=10,
        description="Contenido del post (minimo 10 caracteres)",
        examples=["Este es un contenido valido porque tiene mas de 9 caracteres"],
    )

    @field_validator("title")
    @classmethod
    def not_allowed_title(cls, value: str) -> str:
        forbidden_words = ["porn", "xxx", "spam", "sex"]
        for word in forbidden_words:
            if word in value.lower():
                raise ValueError(f"The title can't content {word}")
        return value


class PostUpdate(BaseModel):
    title: str
    content: str | None = None


# METODOS GET
@app.get("/")
def home():
    return {"message": "welcome to mini blog"}


## query params
@app.get("/posts")
def list_posts(
    query: str | None = Query(
        default=None, description="Search query for blog post title"
    ),
):
    if query:
        results = [post for post in BLOG_POST if query.lower() in post["title"].lower()]
        return {"data": results, "query": query}

    return BLOG_POST


## path params
@app.get("/post/{post_id}")
def get_post(
    post_id: int,
    include_contet: bool = Query(default=True, description="include or not content"),
):
    for post in BLOG_POST:
        if post["id"] == post_id:
            if include_contet:
                return post
            return {"id": post["id"], "title": post["title"]}

    return {"error": "Post not found"}


# METODOS POST
@app.post("/post")
def create_post(post: PostCreate):
    new_id = (BLOG_POST[-1]["id"] + 1) if BLOG_POST else 1
    new_post = {"id": new_id, "title": post.title, "content": post.content}
    BLOG_POST.append(new_post)
    return {"message": "post created", "data": new_post}


# METODO PUT
@app.put("/post/{post_id}")
def update_post(post_id: int, update_data: PostUpdate):
    for post in BLOG_POST:
        if post["id"] == post_id:
            playload = update_data.model_dump(exclude_unset=True)
            if "title" in playload:
                post["title"] = playload["title"]
            if "content" in playload:
                post["content"] = playload["content"]
            return {"message": "Update Post", "data": post}

    raise HTTPException(status_code=404, detail="Post not found")


# METODO DELETE
@app.delete("/post/{post_id}", status_code=204)
def delete_post(post_id: int):
    for index, post in enumerate(BLOG_POST):
        if post["id"] == post_id:
            BLOG_POST.pop(index)
            return
    raise HTTPException(status_code=404, detail="Post not found ")
