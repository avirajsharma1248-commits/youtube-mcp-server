flow = Flow.from_client_config(
    client_config,
    scopes=SCOPES,
    state=state,
    redirect_uri=os.environ["YOUTUBE_REDIRECT_URI"]
)
