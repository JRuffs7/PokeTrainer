import functools

from flask import abort, request

from services import securityservice


def valid_token(f):

  @functools.wraps(f)
  def decorated_function(*args, **kwargs):
    token = request.headers.get('Authorization')
    if not securityservice.ValidateToken(token):
      abort(401)
    return f(*args, **kwargs)

  return decorated_function
