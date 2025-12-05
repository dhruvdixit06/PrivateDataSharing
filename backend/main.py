from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.database import Base, engine
from backend.db import models
from backend.routers import users, roles, user_roles, applications, access, mappings, review

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Access Review POC API v2")

# CORS for local Next.js frontend
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Access Review POC API v2 running"}

app.include_router(users.router)
app.include_router(roles.router)
app.include_router(user_roles.router)
app.include_router(applications.router)
app.include_router(access.router)
app.include_router(mappings.router)
app.include_router(review.router)
