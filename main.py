from fastapi import Body, FastAPI, HTTPException, Query

app = FastAPI(title="Mini Blog")

BLOG_POST = [
    {"id": 1, "title": "First Post", "content": "This is the first post."},
    {"id": 2, "title": "Second Post", "content": "This is the second post."},
    {"id": 3, "title": "Django vs FastAPI", "content": "FastAPI es mas rapido que Django."}
]

# METODOS GET
@app.get("/")
def home():
    return {"message": "welcome to mini blog"}

## query params
@app.get("/posts")
def list_posts(query: str | None=Query(default=None, description="Search query for blog post title")):
    if query:
        results = [post for post in BLOG_POST if query.lower() in post["title"].lower()]
        return {"data": results, "query": query}
    
    return BLOG_POST

## path params
@app.get("/post/{post_id}")
def get_post(post_id: int, include_contet: bool=Query(default=True, description="include or not content")):
    for post in BLOG_POST:
        if post["id"] == post_id: 
            if include_contet:
                return post
            return {"id": post["id"], "title": post["title"]}
    
    return {"error": "Post not found"}

# METODOS POST
@app.post("/post")
def create_post(post: dict=Body(...)):  # noqa: B008
    if "title" not in post or "content" not in post:
        return {"error": "Title or content is required"}

    if not str(post["title"]).strip():
        return {"error": "Title can't be empty"}

    new_id = (BLOG_POST[-1]["id"] + 1) if BLOG_POST else 1
    new_post = {"id": new_id, "tile": post["title"], "content": post["content"]}
    BLOG_POST.append(new_post)
    return {"message": "post created", "data": new_post}

# METODO PUT
@app.put("/post/{post_id}")
def update_post(post_id: int, update_data: dict=Body(...)):  # noqa: B008
    for post in BLOG_POST:
        if post["id"] == post_id and "title" and "content" in update_data:
            post["title"] = update_data["title"]
            post["content"] = update_data["content"]
            return {"message": "Update Post", "data": post}

    raise HTTPException(status_code=404, detail="Post not found")

# METODO DELETE
@app.delete("/post/{post_id}", status_code= 204)
def delete_post(post_id: int):
    for index, post in enumerate(BLOG_POST):
        if post["id"] == post_id:
            BLOG_POST.pop(index)
            return
    raise HTTPException(status_code=404, detail="Post not found ")
    