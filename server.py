from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():
    return {
        "status": "online",
        "service": "YouTube MCP Server"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/oauth/login")
def oauth_login():
    return {
        "status": "oauth_route_working"
    }
