from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time

EMAIL = "24f2006741@ds.study.iitm.ac.in"

app = FastAPI()

# -----------------------
# CORS Middleware
# -----------------------
allowed_origins = [
    "https://app-sxsi1j.example.com",
    "https://exam.sanand.workers.dev"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Request Context Middleware
# -----------------------
class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID")

        if not request_id:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response

app.add_middleware(RequestContextMiddleware)

# -----------------------
# Rate Limiting Middleware
# -----------------------
RATE_LIMIT = 14
WINDOW = 10

client_requests = {}

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_id = request.headers.get("X-Client-ID", "anonymous")
        now = time.time()

        if client_id not in client_requests:
            client_requests[client_id] = []

        client_requests[client_id] = [
            t for t in client_requests[client_id]
            if now - t < WINDOW
        ]

        if len(client_requests[client_id]) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )

        client_requests[client_id].append(now)

        response = await call_next(request)
        return response

app.add_middleware(RateLimitMiddleware)

# -----------------------
# API Endpoint
# -----------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
