class PreserveSessionKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Save current session key before login
        if request.user.is_anonymous:
            request.session[
                'pre_login_session_key'
            ] = request.session.session_key
        response = self.get_response(request)
        return response
