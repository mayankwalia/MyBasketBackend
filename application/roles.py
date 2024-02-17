from functools import wraps
from flask_jwt_extended import get_jwt_identity
from application.models import User


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if current_user and current_user.role_id == 3:
            return fn(*args, **kwargs)
        else:
            return {"message": "Permission denied"}, 403
    return wrapper

def store_manager_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if current_user and current_user.role_id == 2:
            return fn(*args, **kwargs)
        else:
            return {"message": "Permission denied"}, 403
    return wrapper

def owner_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if current_user and current_user.role_id == 2 or current_user.role_id == 3:
            return fn(*args, **kwargs)
        else:
            return {"message": "Permission denied"}, 403
    return wrapper

def customer_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if current_user and current_user.role_id == 1:
            return fn(*args, **kwargs)
        else:
            return {"message": "Permission denied"}, 403
    return wrapper
