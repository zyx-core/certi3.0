from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import your route modules
from app.routes import (
    upload,
    generate,
    extract_excel,
    extract_image,
    email,
    mapping,
)

app = FastAPI(title="Certificate Generator API")

# Enable CORS (allow all for development; restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origin(s) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers with optional prefixes
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(generate.router, prefix="/generate", tags=["Generate"])
app.include_router(email.router, tags=["Email"])
app.include_router(extract_excel.router, tags=["Excel"])
app.include_router(extract_image.router, tags=["Image"])
app.include_router(mapping.router, tags=["Mapping"])


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Certificate Generator API is up and running."}


@app.get("/debug-routes", tags=["Debug"])
def debug_routes():
    """Returns all registered route paths (for testing purposes)."""
    return {"message": "Certificate Generator API is up and running."}
    return [route.path for route in app.router.routes]

