
from application.instances import db, app, cache
from flask import jsonify, request
from flask_jwt_extended import jwt_required, current_user
from datetime import datetime, timedelta
from flask_restful import marshal
from application.models import User, Category, Products, Feedback, Cart, Orders, ItemsOrdered, ManagerRequests
from application.roles import admin_required, store_manager_required, customer_required, owner_required
from .utilities import feedback_resource_fields, products_resource_fields, orders_resource_fields, user_resource_fields, cart_resource_fields, items_ordered_resource_fields, getImageFromEntity
from .utilities import get_all_categories, get_all_products
from sqlalchemy import func, or_


@app.get('/user/<int:user_id>')
@jwt_required()
def get_user(user_id):
    if current_user.id != user_id and current_user.role_id != 3:
        return {'message': 'Permission denied'}, 403
    user = User.query.get(user_id)
    if user:
        serialized_user = marshal(user, user_resource_fields)
        result = jsonify(serialized_user), 200
        return result
    return {'message': 'User not found'}, 404


@app.post('/update-report-preference')
@jwt_required()
@customer_required
def report_preference():
    preference = request.json['reportType']
    if preference not in ['HTML', 'PDF']:
        return {'message': 'Invalid preference'}, 400
    current_user.report_type = preference
    db.session.commit()
    return {'message': 'Report preference updated successfully'}, 200

# ------------------------ Products ------------------------

@app.get('/products/search')
@jwt_required()
def search_products():
    # type can be latest, trending, all, few, out of stock
    type = request.args.get('type', 'all')
    searchTerm = request.args.get('query', '')
    category_id = request.args.get('category_id', '')
    limit = request.args.get('limit', 5, type=int)
    sortBy = request.args.get('sort_by', 'manufacture_date')
    sortDirection = request.args.get('sort_direction', 'desc')
    
    # By default ordered by manufacture date in descending order
    if sortDirection not in ['asc', 'desc']:
        sortDirection = 'desc'
    if sortBy not in ['manufacture_date', 'expiry_date', 'price', 'average_rating', 'title']:
        sortBy = 'manufacture_date'

    ordering = True
    if type == 'latest':
        products = Products.query.order_by(Products.manufacture_date.desc())
        ordering = False
    elif type == 'trending':
        items = ItemsOrdered.query.group_by(ItemsOrdered.item_id).order_by(db.func.count(ItemsOrdered.item_id).desc())
        products_ids = [item.item_id for item in items]
        products = Products.query.filter(Products.id.in_(products_ids))
    elif type == 'popular':
        products = Products.query.order_by(Products.average_rating.desc())
        ordering = False
    elif type == 'few':
        products = Products.query.order_by(Products.stock.asc())
        ordering = False
    elif type == 'out_of_stock':
        products = Products.query.filter(Products.stock == 0)
    elif type == 'all':
        products = Products.query

    if searchTerm != '':
        products = products.filter(or_(Products.title.contains(searchTerm), Products.description.contains(searchTerm)))

    if category_id != '':
        products = products.filter(Products.category_id == category_id)
    if ordering:
        if sortDirection == 'desc':
            products = products.order_by(getattr(Products, sortBy).desc()).limit(limit).all()
        else:
            products = products.order_by(getattr(Products, sortBy).asc()).limit(limit).all()
    else:
        products = products.limit(limit).all()
    if len(products) == 0:
        return {'message': 'No products found'}, 404
    return marshal(products, products_resource_fields),200


@app.get('/products/<int:product_id>/reviews')
@jwt_required()
@cache.memoize(20)
def product_reviews(product_id):
    reviews = Feedback.query.filter_by(product_id=product_id).all()
    if reviews:
        return marshal(reviews, feedback_resource_fields), 200
    return {'message': 'No review found for this product'}, 404

@app.get('/categories/<int:category_id>/products')
@jwt_required()
@cache.memoize(50)
def category_products(category_id):
    products = Products.query.filter_by(category_id=category_id).all()
    if len(products)>0:
        return marshal(products, products_resource_fields), 200
    return {'message': 'No products found for this category'}, 404


@app.post('/product/update-visibility/<int:product_id>')
@jwt_required()
@admin_required
def update_visibility(product_id):
    product = Products.query.get(product_id)
    if product:
        product.visibility = not product.visibility
        db.session.commit()
        cache.delete(f'all_products')
        return {'message': 'Product visibility updated successfully'}, 200
    return {'message': 'Product not found'}, 404


@app.post('/update-discount/<int:productId>')
@jwt_required()
@admin_required
def update_discount(productId):
    product = Products.query.get(productId)
    if product:
        # In percentage
        product.discount = request.json.get('discount') 
        product.discount = min(product.discount, 100)
        db.session.commit()
        cache.delete(f'get_product_{product.id}')
        cache.delete_memoized(category_products, product.category_id)
        return {'message': 'Discount updated successfully'}, 200
    return {'message': 'Product not found'}, 404

# ------------------------ Cart Management ------------------------
@app.post('/add_to_cart/<int:product_id>/quantity/<int:quantity>')
@jwt_required()
@customer_required
def add_to_cart(product_id,quantity=1):
    product = Products.query.get(product_id)
    if product:
        product_in_cart = Cart.query.filter_by(customer_id=current_user.id, product_id=product_id).first()
        if product_in_cart:
            return {'message':  "Product already in cart, try updating the quantity"}, 400
        cart = Cart(customer_id=current_user.id, product_id=product_id, quantity=min(quantity,product.stock))
        db.session.add(cart)
        db.session.commit()
        return {'message': 'Product added to cart successfully'}
    return {'message': 'Product not found'}, 404

@app.post('/update_product_quantity/<int:product_id>/quantity/<int:quantity>')
@jwt_required()
@customer_required
def update_product_quantity(product_id,quantity):
    product = Products.query.get(product_id)
    product_in_cart = Cart.query.filter_by(customer_id=current_user.id, product_id=product_id).first()
    if product_in_cart:
        product_in_cart.quantity = min(quantity,product.stock)
        db.session.commit()
        return {'message': 'Product quantity updated successfully'}
    return {'message': 'Product not found'}, 404

@app.post('/remove_from_cart/<int:product_id>')
@jwt_required()
@customer_required
def remove_from_cart(product_id):
    removed_product = Cart.query.filter_by(customer_id=current_user.id, product_id=product_id).first()
    if removed_product:
        db.session.delete(removed_product)
        db.session.commit()
        return {'message': 'Product removed from cart successfully'}
    return {'message': 'Product not found'}, 404

@app.get('/my-cart')
@jwt_required()
@customer_required
def my_cart():
    items_in_cart = Cart.query.filter_by(customer_id=current_user.id).all()
    return marshal(items_in_cart, cart_resource_fields)

# ------------------------ Order ------------------------
@app.post('/place-order')
@jwt_required()
@customer_required
def place_order():
    items_in_cart = Cart.query.filter_by(customer_id=current_user.id).all()
    if len(items_in_cart) == 0:
        return {'message': 'No items in cart'}, 400
    order = Orders(customer_id=current_user.id)
    current_user.delivery_details = request.json.get('addressDetails')
    db.session.add(order)
    db.session.commit()
    for items in items_in_cart:
        item = ItemsOrdered(order_id=order.id, item_id=items.product_id, quantity=items.quantity, price_per_quantity=items.product.price * (1-items.product.discount/100))
        items.product.stock -= items.quantity
        db.session.add(item)
        db.session.delete(items)
    db.session.commit()
    cache.delete_memoized(track_orders)
    return {'message': 'Order placed successfully'}, 201

@app.get('/track-orders/<int:user_id>')
@jwt_required()
@customer_required
@cache.memoize(10)
def track_orders(user_id):
    if current_user.id != user_id:
        return {'message': 'Permission denied'}, 403
    orders = Orders.query.filter_by(customer_id=user_id).all()
    return marshal(orders, orders_resource_fields)

@app.get('/manager/orders')
@jwt_required()
@owner_required
def placed_orders():
    if current_user.role_id == 3:
        productsOwned = get_all_products()
    else:
        productsOwned = Products.query.filter_by(store_owner_id=current_user.id)
    product_ids = [product.id for product in productsOwned]
    itemsOrdered = ItemsOrdered.query.filter(ItemsOrdered.item_id.in_(product_ids)).all()
    totalSales = sum([item.price_per_quantity*item.quantity for item in itemsOrdered])
    totalQuantitiesSold = sum([item.quantity for item in itemsOrdered])
    return {
        'orders': marshal(itemsOrdered, items_ordered_resource_fields),
        'totalSales': totalSales,
        'totalQuantitiesSold': totalQuantitiesSold,
    }, 200


@app.get('/orders/<int:order_id>/items')
@jwt_required()
@store_manager_required
@cache.memoize(20)
def store_manager_order_items(order_id):
    order = Orders.query.get(order_id)
    if (order.customer_id  == current_user.id) or current_user.role_id == 3:
        return marshal(order.items_ordered, items_ordered_resource_fields)
    return {'message': 'Permission denied'}, 403

@app.get('/manager/products')
@jwt_required()
@store_manager_required
@cache.memoize(20)
def store_manager_products():
    products = Products.query.filter_by(store_owner_id=current_user.id).all()
    for product in products:
        product.image_file = getImageFromEntity(product)
    return marshal(products, products_resource_fields), 200



@app.put('/update-order-status/<int:order_id>')
@jwt_required()
def update_order_status(order_id):
    status = request.args.get('status')
    if status not in ['Transit', 'Delivered', 'Cancelled', 'Pending', 'Returned']:
        return {'message': 'Invalid status'}, 400
    order = Orders.query.get(order_id)
    if current_user.role_id == 1:
        if (current_user.id != order.customer_id and status != 'Cancelled'):
            return {'message': 'Permission denied'}, 403
    order.status = status
    cache.delete_memoized(track_orders, order.customer_id)
    db.session.commit()
    return {'message': 'Order status updated successfully'}, 200

# ------------------------ Manager Requests ------------------------
@app.post('/requests/<int:id>/approve')
@jwt_required()
@admin_required
def approve_request(id):
    request = ManagerRequests.query.get(id)
    try :
        if (request.type == 'Add Category'):
            category = Category(name=request.title, description=request.description, owner_id=request.user_id, approved=True)
            db.session.add(category)
            db.session.delete(request)
        elif (request.type == 'Update Category'):
            category = Category.query.get(request.relatedId)
            category.name = request.title
            category.description = request.description
            db.session.delete(request)
        elif (request.type == 'Remove Category'):
            category = Category.query.get(request.relatedId)
            delete_products = bool(request.description.split(':')[1] == 'true')
            products = category.products
            if not delete_products:
                for product in products:
                    # Setting products category to default category
                    product.category_id = 1
                    db.session.add(product)
                db.session.commit()
            else:
                for product in products:
                    db.session.delete(product)
                db.session.commit()
            db.session.delete(category)
            db.session.commit()
            if not delete_products:
                cache.delete_memoized(category_products, category.id)
            cache.delete('all_categories')
            db.session.delete(category)
            db.session.delete(request)
        elif (request.type == 'Approve Manager'):
            user = User.query.get(request.user_id)
            user.approved = True
            db.session.delete(request)
        else:
            return {'message': 'Invalid request type'}, 400
        cache.delete(f'all_manager_requests')
        db.session.commit()
        if 'Category' in request.type:
            cache.delete(f'get_categories_')
            cache.delete(f'get_categories_{request.relatedId}')
        return {'message': 'Request approved successfully'}
    except Exception as e:
        print("Error",e)
    return {'message': 'Request not found'}, 404

@app.delete('/requests/<int:id>/decline')
@jwt_required()
@admin_required
def decline_request(id):
    request = ManagerRequests.query.get(id)
    try :
        db.session.delete(request)
        db.session.commit()
        cache.delete(f'all_manager_requests')
        return {'message': 'Request removed successfully'}
    except :
        return {'message': 'Request not found'}, 404

# ------------------------ User Management ------------------------
@app.post('/deactivate/<int:id>')
@jwt_required()
def deactivate(id):
    if current_user.role.id != 3 and current_user.id != id:
        return {"message": "Permission denied"}, 403
    user = User.query.get(id)
    if user:
        if user.role_id == 3:
            return {"message": "Cannot deactivate admin account"}, 403
        user.active = False
        db.session.commit()
        cache.delete('all_users')
        return {'message': 'Account deactivated successfully'}
    return {'message': 'Account not found'}, 404

@app.post('/reactivate/<int:id>')
@jwt_required()
@admin_required
def reactivate(id):
    user = User.query.get(id)
    if user:
        if user.role_id == 3:
            return {"message": "Cannot reactivate admin account"}, 403
        user.active = True
        cache.delete('all_users')
        db.session.commit()
        return {'message': 'Account reactivated successfully'}
    return {'message': 'Account not found'}, 404

# ------------------------ Manager Dashboard ------------------------
@app.get('/summary/items-sold')
@jwt_required()
@store_manager_required
@cache.cached(timeout=20, key_prefix='items_sold')
def summary_items_sold():
    now = datetime.utcnow()
    # Create a list of dates for the past 7 days
    dates = [(now - timedelta(days=i)).date() for i in range(7)]
    items_data={}
    productsOwnedIds = [product.id for product in Products.query.filter_by(store_owner_id=current_user.id).all()]
    productTitle = [product.title for product in Products.query.filter_by(store_owner_id=current_user.id).all()]
    for date in dates:
        orders = Orders.query.filter(Orders.created_at >= date, Orders.created_at < date + timedelta(days=1)).all()
        items_data[date.isoformat()] = {}
        count = 0
        for title in productTitle:
            items_data[date.isoformat()][title] = 0
        for order in orders:
            for item in order.items_ordered:
                if item.item_id not in productsOwnedIds:
                    continue
                items_data[date.isoformat()][item.item.title] += item.quantity
                count += item.quantity
            items_data[date.isoformat()]['total'] = count
        if (len(orders)==0):
            items_data[date.isoformat()]['total'] = 0
    return jsonify(items_data),200

# ------------------------ Admin Dashboard ------------------------
@app.get('/summary/orders-placed')
@jwt_required()
@admin_required
@cache.cached(timeout=20, key_prefix='orders_placed')
def summary_order_placed():
    product_ids = [product.id for product in get_all_products()]
    itemsOrdered = ItemsOrdered.query.filter(ItemsOrdered.item_id.in_(product_ids)).all()
    totalSales = sum([item.price_per_quantity*item.quantity for item in itemsOrdered])
    totalQuantitiesSold = sum([item.quantity for item in itemsOrdered])
    now = datetime.utcnow()
    # Create a list of dates for the past 7 days
    dates = [(now - timedelta(days=i)).date() for i in range(7)]
    orders_data={}
    for date in dates:
        count = Orders.query.filter(Orders.created_at >= date, Orders.created_at < date + timedelta(days=1)).count()
        orders_data[date.isoformat()] = count
    order_status_data = {}
    for status in ['Transit', 'Delivered', 'Cancelled', 'Pending', 'Returned']:
        order_status_data[status] = Orders.query.filter_by(status=status).count()
    return jsonify({'orders':orders_data, 'status':order_status_data,'totalSales': totalSales,'totalQuantitiesSold': totalQuantitiesSold,}),200


@app.get('/summary/categories')
@jwt_required()
@owner_required
def summary_category_products():
    category_product_count_dict = {}
    starting_date = request.args.get('starting_date', datetime.utcnow() - timedelta(days=7))
    ending_date = request.args.get('ending_date', datetime.utcnow())
    categories = get_all_categories()
    for category in categories:
        query = Products.query.filter_by(category_id=category.id).filter(
            Products.manufacture_date >= starting_date, Products.manufacture_date <= ending_date
        )
        # Filter the summary data for the store manager. Showing only the products owned by the store manager. For admin it shows all the products.
        if current_user.role_id == 2:
            query = query.filter_by(store_owner_id=current_user.id)
        category_product_count_dict[category.name] = query.count()
    return category_product_count_dict, 200

@app.get('/summary/sales')
@jwt_required()
def summary():
    if current_user.role_id == 3:
        productsOwned = get_all_products()
    elif current_user.role_id == 2:
        productsOwned = Products.query.filter_by(store_owner_id=current_user.id).all()
    else:
        return {"message": "Permission denied"}, 403
    sold_count_dict = {}
    starting_date = request.args.get('starting_date', datetime.utcnow() - timedelta(days=7))
    ending_date = request.args.get('ending_date', datetime.utcnow())
    eligible_order_ids = [
        order_id for order_id, in (
            db.session.query(Orders.id)
            .filter(Orders.created_at >= starting_date, Orders.created_at <= ending_date)
            .all()
        )
    ]
    for product in productsOwned:
        sold_count_dict[product.title] = ItemsOrdered.query.filter(
            ItemsOrdered.item_id == product.id,
            ItemsOrdered.order_id.in_(eligible_order_ids)
        ).with_entities(func.sum(ItemsOrdered.quantity)).scalar()
    return jsonify(sold_count_dict), 200
