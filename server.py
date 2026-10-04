@app.get("/oauth/login")
def oauth_login():

    state = secrets.token_urlsafe(32)

    flow = create_google_flow(state=state)

    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state
    )

    oauth_sessions[state] = flow

    return RedirectResponse(authorization_url)


@app.get("/oauth/callback")
def oauth_callback(code: str, state: str):

    flow = oauth_sessions.pop(state, None)

    if flow is None:
        return JSONResponse(
            {
                "status": "error",
                "message": "OAuth session expired. Please start login again."
            },
            status_code=400
        )

    try:

        # Explicitly don't use PKCE
        flow.fetch_token(
            code=code,
            include_client_id=True
        )

        credentials = flow.credentials

        return JSONResponse({
            "status": "success",
            "message": "YouTube authorization successful",
            "access_token_received": bool(credentials.token),
            "refresh_token_received": bool(credentials.refresh_token)
        })

    except Exception as e:

        return JSONResponse(
            {
                "status": "error",
                "message": str(e)
            },
            status_code=500
        )
