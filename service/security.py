from bottle import (
    request,
    abort,
)

from config_finder import cfg

def restricted(handler):
    """ Only allow whitelisted access to handler """
    def restricted_handler(*args, **kwargs):
        """ check the request for an authorized email then call the hander """
        whitelist = cfg('whitelist', '').split(',')
        try:
            auth_email = request.headers.get('X-Authenticated-Email')
            assert auth_email in whitelist
        except:
            abort(401, "Not Authorized")
            return
        return handler(*args, **kwargs)

    return restricted_handler

