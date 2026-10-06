@app.get("/oauth/callback")
async def oauth_callback(code: str, state: str = None):

    try:
        flow = create_google_flow(state=state)

        flow.fetch_token(code=code)

        credentials = flow.credentials

        access_token = credentials.token
        refresh_token = credentials.refresh_token

        if not refresh_token:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Refresh token was not received. Try OAuth authorization again."
                }
            )

        # Temporary process storage
        os.environ["YOUTUBE_ACCESS_TOKEN"] = access_token
        os.environ["YOUTUBE_REFRESH_TOKEN"] = refresh_token

        # IMPORTANT:
        # Temporary page to copy the refresh token into Render Environment Variables.
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>YouTube Authorization</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 900px;
                    margin: 50px auto;
                    padding: 20px;
                }}
                .warning {{
                    background: #fff3cd;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                code {{
                    display: block;
                    background: #f4f4f4;
                    padding: 15px;
                    word-break: break-all;
                    border-radius: 8px;
                    margin: 10px 0;
                }}
                button {{
                    padding: 12px 20px;
                    cursor: pointer;
                    font-size: 16px;
                }}
            </style>
        </head>

        <body>

        <h1>✅ YouTube Authorization Successful</h1>

        <div class="warning">
            <strong>IMPORTANT:</strong>
            This refresh token is private. Do NOT share it with anyone.
        </div>

        <h2>Step 1 — Copy this Refresh Token</h2>

        <code id="token">{refresh_token}</code>

        <button onclick="copyToken()">Copy Refresh Token</button>

        <h2>Step 2 — Add it to Render</h2>

        <p>
        Render → Your Service → Environment → Add Environment Variable
        </p>

        <code>
        YOUTUBE_REFRESH_TOKEN
        </code>

        <p>
        Value = the refresh token shown above
        </p>

        <h2>Step 3</h2>

        <p>
        After adding the variable to Render, redeploy the service.
        </p>

        <script>
        function copyToken() {{
            const token = document.getElementById("token").innerText;
            navigator.clipboard.writeText(token);
            alert("Refresh token copied.");
        }}
        </script>

        </body>
        </html>
        """

        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        )
