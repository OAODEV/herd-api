from bottle import (
    request,
    abort,
)

from config_finder import cfg

def restricted(handler):
    """ Only allow CI token access to handler """
    def restricted_handler(*args, **kwargs):
        """ check the request for an authorized email then call the hander """
        try:
            auth_token = request.headers.get('X-Authenticated-Token')
            assert auth_token == "CI"
        except:
            abort(401, "Not Authorized")
            return
        return handler(*args, **kwargs)

    return restricted_handler

