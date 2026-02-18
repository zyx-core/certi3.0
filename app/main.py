from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Import your route modules
from app.routes import (
    upload,
    generate,
    extract_excel,
    extract_image,
    email,
    mapping,
    test_email,
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
app.include_router(test_email.router, prefix="/test", tags=["Debug"])


@app.get("/api", tags=["Root"])
def read_root():
    return {"message": "Certificate Generator API is up and running."}

@app.get("/health", tags=["Root"])
def health_check():
    return {"status": "healthy"}

@app.get("/")
async def serve_home():
    # Serve the index.html from the static directory
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Web app not found. Please build Flutter app."}


@app.get("/debug-routes", tags=["Debug"])
def debug_routes():
    """Returns all registered route paths (for testing purposes)."""
    return [route.path for route in app.router.routes]


# --- Serve Flutter Static Files ---

# Mount the static directory (ensure 'app/static' exists and contains Flutter build)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Catch-all route for SPA (Serve index.html for non-API routes)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow API routes to pass through (handled above)
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
             return {"error": "Not Found", "message": "API route not found"}
        
        # Check if file exists in static (e.g. flutter.js, manifest.json)
        file_path = os.path.join(static_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
             return FileResponse(file_path)

        # Default to index.html for client-side routing
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"error": "Frontend not found", "message": "Please build flutter web and copy to app/static"}
else:
    print(f"Directory {static_dir} does not exist. Skipping static files mount.")


