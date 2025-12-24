"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Conto Test App",
    description="A sandbox application for testing Conto PR review signals",
    version="0.1.0",
)

app.include_router(router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
