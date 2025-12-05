from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.database import Base, engine
from backend.routers import users, roles, user_roles, applications, access, review, auth, mappings

# create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Access Review POC API - v2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(user_roles.router)
app.include_router(applications.router)
app.include_router(access.router)
app.include_router(mappings.router)
app.include_router(review.router)

@app.get("/")
def root():
    return {"message": "Access Review POC API v2 running"}
