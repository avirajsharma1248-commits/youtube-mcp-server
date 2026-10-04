@app.get("/oauth/login")
def oauth_login():
    return {
        "status": "oauth_route_working"
    }
