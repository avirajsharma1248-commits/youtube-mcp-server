import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "YouTube MCP Server"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/mcp")
def mcp():
    return JSONResponse({
        "name": "youtube-mcp-server",
        "status": "ready"
    })
