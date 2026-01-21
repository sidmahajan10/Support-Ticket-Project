from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Session authentication without CSRF enforcement.

    Why: DRF's SessionAuthentication enforces CSRF checks on "unsafe" methods
    (POST/PATCH/PUT/DELETE). For a SPA (React) calling the API with cookies,
    it's common to either:
      - include CSRF tokens in every request, OR
      - disable CSRF enforcement for API endpoints and rely on authentication +
        same-origin/cors constraints during development.

    This class implements the latter.
    """

    def enforce_csrf(self, request):
        return  # CSRF checks are intentionally disabled for API requests.

