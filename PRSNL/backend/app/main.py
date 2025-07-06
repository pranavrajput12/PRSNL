from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from .api import capture, search, timeline

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(capture.router, prefix="/api")
# app.include_router(search.router, prefix="/api")
# app.include_router(timeline.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "PRSNL Backend"}
