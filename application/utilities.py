from flask_restful import reqparse, fields
from .models import User, Products, Category, ManagerRequests
from .instances import cache

# It returns the image data in base64 format
def getImageFromEntity(entity):
    import os
    from application.instances import app
    import base64
    # Entity can be user or product
    image_path = entity.image
    if image_path:
        with open(os.path.join(app.config['UPLOAD_FOLDER'], image_path), 'rb') as f:
            image_data = base64.b64encode(f.read())
        return image_data
    else:
        return ''

# These functions are used to get all the data from the database and cache it
@cache.cached(timeout=20, key_prefix='all_products')
def get_all_products():
    products = Products.query.all()
    for product in products:
        product.image_file = getImageFromEntity(product)
    return products

@cache.cached(timeout=20, key_prefix='all_categories')
def get_all_categories():
    categories = Category.query.all()
    return categories

@cache.cached(timeout=20, key_prefix='all_users')
def get_all_users():
    users = User.query.all()
    return users

@cache.cached(timeout=20, key_prefix='all_manager_requests')
def get_all_manager_requests():
    requests = ManagerRequests.query.all()
    return requests

# Parsers for the API

# User parser
user_parser = reqparse.RequestParser()
user_parser.add_argument('username', type=str, required=True, help='Username is required')
user_parser.add_argument('password', type=str, required=True, help='Password is required')
user_parser.add_argument('email', type=str, required=True, help='Email is required')
user_parser.add_argument('created_at', type=str)
user_parser.add_argument('last_activity', type=str)
user_parser.add_argument('approved', type=bool)
user_parser.add_argument('active', type=bool)
user_parser.add_argument('role_id', type=int, required=True, help='Role ID is required')

# Product parser
product_parser = reqparse.RequestParser()
product_parser.add_argument('title', type=str, required=True, help='Title is required')
product_parser.add_argument('description', type=str)
product_parser.add_argument('price', type=float, required=True, help='Price is required')
product_parser.add_argument('image', type=str)
product_parser.add_argument('store_owner_id', type=int, required=False, help='Store owner ID is required')
product_parser.add_argument('approved', type=bool, default=False)
product_parser.add_argument('category_id', type=int, required=True, help='Category ID is required')
product_parser.add_argument('visibility', type=bool, default=False)
product_parser.add_argument('stock', type=int, required=True, help='Stock quantity is required')
product_parser.add_argument('unit', type=str)
product_parser.add_argument('discount', type=int)

# Category parser
category_parser = reqparse.RequestParser()
category_parser.add_argument('name', type=str, required=True, help='Name is required')
category_parser.add_argument('description', type=str)
category_parser.add_argument('owner_id', type=int, required=False, help='Owner ID is required')

# Feedback parser
feedback_parser = reqparse.RequestParser()
feedback_parser.add_argument('product_id', type=int, required=True, help='Product ID is required')
feedback_parser.add_argument('review', type=str)
feedback_parser.add_argument('rating', type=float, required=True, help='Rating is required')

# Manager request parser
manager_request_parser = reqparse.RequestParser()
manager_request_parser.add_argument('type', type=str, required=True, help='Request type is required')
manager_request_parser.add_argument('title', type=str, required=True, help='Title is required')
manager_request_parser.add_argument('description', type=str, required=True, help='Description is required')
manager_request_parser.add_argument('relatedId', type=str, required=False)

# Order parser
order_parser = reqparse.RequestParser()
order_parser.add_argument('customer_id', type=int, required=True, help='Customer ID is required')
order_parser.add_argument('status', type=str)

# Resource fields for the API


test_api_response_fields = {
    'message': fields.String,
}

user_resource_fields = {
    'id': fields.Integer,
    'username': fields.String,
    'email': fields.String,
    'created_at': fields.DateTime,
    'approved': fields.Boolean,
    'active': fields.Boolean,
    'role_id': fields.Integer,
    'report_type': fields.String,
}
user_fields = {
    'id': fields.Integer,
    'username': fields.String,
    'email': fields.String,
}

manager_request_resource_fields = {
    'id': fields.Integer,
    'type': fields.String,
    'title': fields.String,
    'description': fields.String,
    'relatedId': fields.Integer,
    'user': fields.Nested(user_fields),
}

products_resource_fields = {
    'id': fields.Integer,
    'title': fields.String,
    'description': fields.String,
    'price': fields.Float,
    'image': fields.String,
    'store_owner_id': fields.Integer,
    'category_id': fields.Integer,
    'visibility': fields.Boolean,
    'discount': fields.Float,
    'initialStock': fields.Integer,
    'stock': fields.Integer,
    'unit': fields.String,
    'manufacture_date': fields.DateTime,
    'expiry_date': fields.DateTime,
    'image_file': fields.String,
    'average_rating': fields.Float,
    'store_owner': fields.Nested(user_fields),
}
product_fields = {
    'id': fields.Integer,
    'title': fields.String,
}

feedback_resource_fields = {
    'id': fields.Integer,
    'user': fields.Nested(user_fields),
    'product_id': fields.Integer,
    'review': fields.String,
    'rating': fields.Float,
    'created_at': fields.DateTime,
    'updated_at': fields.DateTime,
}

order_fields = {
    'id': fields.Integer,
    'customer': fields.Nested(user_fields),
    'status': fields.String,
    'created_at': fields.DateTime,
    'updated_at': fields.DateTime,
}
items_ordered_resource_fields = {
    'id': fields.Integer,        
    'item':fields.Nested(product_fields),
    'quantity': fields.Integer,
    'price_per_quantity': fields.Float,
    'order': fields.Nested(order_fields)
}
orders_resource_fields = {
    'id': fields.Integer,
    'customer_id': fields.Integer,
    'status': fields.String,
    'created_at': fields.DateTime,
    'updated_at': fields.DateTime,
    'customer': fields.Nested(user_fields),
    'items_ordered': fields.List(fields.Nested(items_ordered_resource_fields))
}

cart_resource_fields = {
    'id': fields.Integer,
    'user_id': fields.Integer,
    'quantity': fields.Integer,
    'product': fields.Nested(products_resource_fields)
}

categories_resource_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'description': fields.String,
    'owner': fields.Nested(user_fields),
    'approved': fields.Boolean
}



