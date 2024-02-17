
from flask_restful import Resource, reqparse, marshal, request, marshal_with
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from .instances import db, app
from flask_jwt_extended import jwt_required, current_user, create_access_token
from application.roles import admin_required, customer_required, store_manager_required, owner_required
from application.models import User, Products, Category, ManagerRequests, Feedback, Cart
import os
from .utilities import getImageFromEntity, categories_resource_fields, category_parser, products_resource_fields, user_resource_fields, manager_request_resource_fields, manager_request_parser, test_api_response_fields, feedback_parser, feedback_resource_fields, feedback_resource_fields, user_fields
from .utilities import get_all_categories, get_all_products, get_all_users, get_all_manager_requests
from datetime import datetime
from .instances import cache
from .controllers import category_products, product_reviews



class TestAPI(Resource):
    @marshal_with(test_api_response_fields)
    def get(self):
        return {"message": "Hello"}, 200

class SignupAPI(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('customer', type=bool, required=False)
        data = parser.parse_args()

        # Check if the username is already in use
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            return {'message': 'Username already in use'}, 400
        
        new_user = User(
            username=data['username'],
            password=generate_password_hash(data['password']),
            email=data['email'],
            role_id = 1 if data['customer'] == True else 2, # Customer role id is 1 and store manager role id is 2
            approved = True if data['customer'] == True else False # Customer do not require admin approval for signup
        )
        db.session.add(new_user)
        db.session.commit()

        # Add a request for admin approval if the user is a store manager
        if (data['customer'] == False):
            request = ManagerRequests(type='Approve Manager', title='Approve Manager', description=f'New Manager signup: {new_user.username}', relatedId=new_user.id, user_id=new_user.id)
            db.session.add(request)
            db.session.commit()

        new_user.update_last_activity()
        serialized_user = marshal(new_user, user_resource_fields)
        access_token = create_access_token(identity=new_user.username)
        return {'message': 'User registered successfully', 'access_token': access_token, 'user': serialized_user}, 201

class LoginAPI(Resource):
    def post(self):
        if not request.json:
            return {'message': 'Bad request'}, 400
        if not request.json['username'] or not request.json['password']:
            return {'message': 'Username and password are required'}, 400
        
        user = User.query.filter_by(username=request.json['username']).first()
        if user and check_password_hash(user.password, request.json['password']):
            if user.active == False:
                return {'message': 'User is inactive. Ask admin to activate this account'}, 403
            access_token = create_access_token(identity=user.username)
            serialized_user = marshal(user, user_resource_fields)
            user.update_last_activity()
            return {'access_token': access_token, 'user': serialized_user}, 200
        return {'message': 'Invalid credentials'}, 401

class UsersAPI(Resource):
    @jwt_required()
    def get(self, user_id = None):
        users = get_all_users()
        # If the user is not admin, return only the essential details otherwise return all details
        # Role id 3 is for admin
        if current_user.role_id != 3:
            serialized_users = [marshal(user, user_fields) for user in users]
        else:
            serialized_users = [marshal(user, user_resource_fields) for user in users]
        return serialized_users, 200

    @jwt_required()
    def put(self, user_id):
        # For updating user password
        if current_user.id != user_id:
            return {"message": "Permission denied"}, 403
        old_password = request.json.get('old_password', None)
        new_password = request.json.get('new_password', None)
        if (old_password is None or new_password is None):
            return {'message': 'Old password and new password are required'}, 400
        if (check_password_hash(current_user.password, old_password) == False):
            return {'message': 'Old password is incorrect'}, 400
        current_user.password = generate_password_hash(new_password)
        current_user.update_last_activity()
        db.session.commit()
        cache.delete('all_users')
        # Generate a new access token for the user
        access_token = create_access_token(identity=current_user.username)
        return {'message': 'User updated successfully', 'access_token': access_token, 'user': marshal(current_user,user_resource_fields)}, 201

class ProductsAPI(Resource):
    @jwt_required()
    @cache.memoize(10)
    def get(self, product_id = None):
        if product_id is not None:
            product = Products.query.get(product_id)
            if product:
                product.image_file = getImageFromEntity(product)
                return marshal(product, products_resource_fields),200
            else:
                return {'message': 'Product not found'}, 404
        else:
            products = get_all_products()
            return marshal(products, products_resource_fields),200

    @jwt_required()
    @owner_required
    def post(self):
        data = request.form
        try:
            # If category_id is provided by store owner, it is set to default category
            if 'category_id' not in data:
                data['category_id'] = 1
            if 'image' in request.files:
                filename = secure_filename(request.files['image'].filename)
                img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image = request.files['image']
                image.save(img_path)
            else:
                filename = ''
            product = Products(     
                title = data['title'],
                description = data['description'],
                price =data['price'],
                unit = 'kg',
                image = filename,
                category_id = data['category_id'],
                initialStock = data['stock'], stock=data['stock'],
                discount = data['discount'])
            if data['manufacture_date']:
                product.manufacture_date = datetime.fromisoformat(data['manufacture_date'])
            if data['expiry_date']:
                product.expiry_date = datetime.fromisoformat(data['expiry_date'])
            # Currently product is automatically approved if the store owner is creating it.
            product.approved = True
            product.store_owner_id = current_user.id
            db.session.add(product)
            db.session.commit()
            cache.delete_memoized(category_products, product.category_id)
            cache.delete('all_products')
            return marshal(product, products_resource_fields), 201
        except Exception as e:
            print("Error",e)
            return {'message': 'Error in creating product'}, 500
    
    @jwt_required()
    @store_manager_required
    def put(self, product_id):
        # Only owner of the product can update the product
        product = Products.query.get(product_id)
        if product:
            if (current_user.id != product.store_owner_id):
                return {"message": "Permission denied"}, 403
            data = request.form
            # Handle image upload
            if 'image' in request.files and request.files['image'].filename != '':
                filename = secure_filename(request.files['image'].filename)
                img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image = request.files['image']
                product.image = filename
                image.save(img_path)
            for key, value in data.items():
                if key in ['title', 'description', 'price', 'category_id', 'stock', 'unit', 'manufacture_date', 'expiry_date', 'discount']:
                    if value and value!='':
                        if key =='manufacture_date' or key == 'expiry_date':
                            # Handling date fields
                            value = datetime.fromisoformat(value)
                        setattr(product, key, value)
            db.session.commit()
            cache.delete_memoized(category_products, product.category_id)
            cache.delete('all_products')
            return marshal(product, products_resource_fields), 201
        return {'message': 'Product not found'}, 404

    @jwt_required()
    @owner_required
    def delete(self, product_id = None):
        if product_id is None:
            return {'message': 'Product id is required'}, 400
        product = Products.query.get(product_id)
        if product is None:
            return {'message': 'Product not found'}, 404
        # Either store manager or admin can delete the product
        if (current_user.id != product.store_owner_id) and current_user.role_id != 3:
            return {"message": "Permission denied"}, 403
        # Deleting all associated records in feedback, cart and orders related to this product. So that the product can be deleted.
        for item in product.orders_placed:
            db.session.delete(item)
        cartItems = Cart.query.filter_by(product_id=product_id).all()
        for item in cartItems:
            db.session.delete(item)
        for feedback in product.feedbacks:
            db.session.delete(feedback)
        db.session.delete(product)
        db.session.commit()
        cache.delete_memoized(category_products, product.category_id)
        cache.delete('all_products')
        return {'message': 'Product deleted successfully'}, 200

class CategoriesAPI(Resource):
    @jwt_required()
    def get(self):
        categories = get_all_categories()
        result = marshal(categories, categories_resource_fields), 200
        return result

    @jwt_required()
    @admin_required
    def post(self):
        args = category_parser.parse_args()
        category = Category(**args)
        # If admin is creating a category, it is automatically approved
        category.approved = True
        category.owner_id = current_user.id
        db.session.add(category)
        db.session.commit()
        cache.delete('all_categories')
        return marshal(category, categories_resource_fields), 201

    @jwt_required()
    @admin_required
    def put(self, category_id = None):
        if category_id is None:
            return {'message': 'Category id is required'}, 400
        category = Category.query.get(category_id)
        if category:
            for key, value in request.json.items():
                if key in ['name', 'description', 'owner_id', 'approved']:
                    setattr(category, key, value)
            db.session.commit()
            cache.delete('all_categories')
            return marshal(category, categories_resource_fields), 201
        return {'message': 'Category not found'}, 404

    @jwt_required()
    @admin_required
    def delete(self, category_id = None):
        if category_id is None:
            return {'message': 'Category id is required'}, 400
        # Whether to delete products in the category or not
        # If not, the products will be moved to default category
        delete_products = request.json.get('deleteProducts', False)
        category = Category.query.get(category_id)

        if category:
            products = Products.query.filter_by(category_id=category_id).all()
            if not delete_products:
                for product in products:
                    # Setting product's category to default category
                    # 1 is the id of default category
                    product.category_id = 1
                    db.session.add(product)
                db.session.commit()
            else:
                # Delete each product individually
                for product in products:
                    db.session.delete(product)
            db.session.delete(category)
            db.session.commit()
            if not delete_products:
                cache.delete_memoized(category_products, category_id)
            cache.delete('all_categories')
            return {'message': 'Category deleted successfully'}, 200
        return {'message': 'Category not found'}, 404

class FeedbackAPI(Resource):
    @jwt_required()
    @customer_required
    def post(self):
        args = feedback_parser.parse_args()
        feedback = Feedback(**args)
        feedback.user_id = current_user.id
        product = Products.query.get(feedback.product_id)
        db.session.add(feedback)
        db.session.commit()
        product.compute_average_rating()
        current_user.update_last_activity()
        db.session.commit()
        feedback.user_id=current_user.id
        cache.delete_memoized(product_reviews,feedback.product_id)
        return marshal(feedback, feedback_resource_fields), 201

    @jwt_required()
    def delete(self, feedback_id):
        feedback = Feedback.query.get(feedback_id)
        if feedback:
            # If the user is not admin, check if the feedback belongs to the user
            if (current_user.id != feedback.user_id) and current_user.role_id != 3:
                return {"message": "Permission denied"}, 403
            product = Products.query.get(feedback.product_id)
            db.session.delete(feedback)
            db.session.commit()
            product.compute_average_rating()
            db.session.commit()
            cache.delete_memoized(product_reviews,feedback.product_id)
            return {'message': 'Feedback deleted successfully'}, 200
        return {'message': 'Feedback not found'}, 404

class ManagerRequestsAPI(Resource):
    @jwt_required()
    @admin_required
    def get(self):
        requests = get_all_manager_requests()
        return marshal(requests, manager_request_resource_fields), 200

    @jwt_required()
    @store_manager_required
    def post(self):
        args = manager_request_parser.parse_args()
        request = ManagerRequests(**args)
        request.user_id = current_user.id
        db.session.add(request)
        db.session.commit()
        cache.delete('all_manager_requests')
        return marshal(request, manager_request_resource_fields), 201

    @jwt_required()
    @admin_required
    def put(self, request_id):
        request = ManagerRequests.query.get(request_id)
        if request:
            args = manager_request_parser.parse_args()
            for key, value in args.items():
                setattr(request, key, value)
            db.session.commit()
            cache.delete('all_manager_requests')
            return marshal(request, manager_request_resource_fields), 201
        return {'message': 'Manager request not found'}, 404

    @jwt_required()
    @admin_required
    def delete(self, request_id):
        request = ManagerRequests.query.get(request_id)
        if request:
            db.session.delete(request)
            db.session.commit()
            cache.delete('all_manager_requests')
            return {'message': 'Manager request deleted successfully'}, 200
        return {'message': 'Manager request not found'}, 404
