from app import app as flask_app


def main(request):
    """Entry point for Cloud Run Functions (HTTP)."""
    with flask_app.request_context(request.environ):
        return flask_app.full_dispatch_request()
