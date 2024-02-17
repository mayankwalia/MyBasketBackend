
from application.config import LocalDevelopmentConfig
from .instances import db, api, mail, app, cache
from flask_jwt_extended import JWTManager
from .models import User, Role, Products, Category, Orders, ItemsOrdered, Cart, Feedback
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from flask_restful import Api
from application.workers import celery_init_app


def create_app():
    print("----- Starting the local development -----")
    # Configures the LocalDevelopmentConfig data with the app
    app.config.from_object(LocalDevelopmentConfig)
    app.config.from_mapping(
        CELERY=dict(
                broker_url = 'redis://localhost:6379/0',
                result_backend = 'redis://localhost:6379/1',
                task_ignore_result = False,
                broker_connection_retry_on_startup = True,
                timezone = "Asia/kolkata"
        )
    )
    db.init_app(app)
        
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/1'
    # Create celery instance
    celery = celery_init_app(app)

    jwt = JWTManager(app)
    api = Api(app)
    CORS(app)
    mail.init_app(app)
    app.app_context().push()
    cache.init_app(app)
    app.app_context().push()
    with app.app_context():
        initialise_database(app)
    
    return app, jwt, api, celery


# --------------- Setting up the database --------------- #
def initialise_database(app):
   with app.app_context():
        from random import randint, randrange, choice
        from datetime import datetime, timedelta
        inspector = db.inspect(db.engine)
        table_names = inspector.get_table_names()
        # If no tables exist
        if not table_names:  
            description='At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident, similique sunt in culpa qui officia deserunt mollitia animi, id est laborum et dolorum fuga. Et harum quidem rerum facilis est et expedita distinctio.'
            db.create_all()
            admin_role = Role(name="Admin")
            customer_role = Role(name="Customer")
            store_manager_role = Role(name="Store Manager")

            db.session.add(customer_role)
            db.session.add(store_manager_role)
            db.session.add(admin_role)
            db.session.commit()

            # Create users
            admin_user = User(username="admin", password=generate_password_hash("password"), email="admin@yopmail.com", role=admin_role, approved=True)
            customer_user = User(username="customer", password=generate_password_hash("password"), email="customer@yopmail.com", role=customer_role, approved=True)
            new_customer = User(username="newcustomer", password=generate_password_hash("password"), email="newcustomer@yopmail.com", role=customer_role, approved=True)
            manager_user = User(username="manager", password=generate_password_hash("password"), email="manager@yopmail.com", role=store_manager_role, approved=True)
            unapproved_manager_user = User(username="unapproved", password=generate_password_hash("password"), email="unapproved@yopmail.com", role=store_manager_role, approved=False)

            db.session.add(admin_user)
            db.session.add(customer_user)
            db.session.add(new_customer)
            db.session.add(manager_user)
            db.session.add(unapproved_manager_user)

            default_category = Category(name="Uncategorized", description=description, owner=admin_user, approved=True)
            category1 = Category(name="Vegetables & Fruits", description=description, owner=manager_user, approved=True)
            category2 = Category(name="Bakery, Cakes & Dairy", description=description, owner=manager_user, approved=True)
            category3 = Category(name="Snacks", description=description, owner=manager_user, approved=True)
            category4 = Category(name="Beverages", description=description, owner=manager_user, approved=True)
            category5 = Category(name="Staples", description=description, owner=manager_user, approved=True)

            db.session.add(default_category)
            db.session.add(category1)
            db.session.add(category2)
            db.session.add(category3)
            db.session.add(category4)
            db.session.add(category5)

            # Create products
            products = {
                1: ["Beetroot","Beets","Carrot","Cloudberry","GingerRoot","OnionYellow","Pumpkin","WholeKiwi","ZucchiniCousaSquash","Tomatoes"],
                2: ["BreadGarlic","Nuggets"],
                3: ["Samosa","McCain","FrenchFries"],
                4: ["Boost","Ensure","Horlicks","Chocolate Drink","BadamMix"],
                5: ["CornFlour","Rice","Multigrains","Sooji","Atta"],
            }
            for key, products in products.items():
                extension = '.webp'
                if key == 1:
                    extension = '.png'
                for product in products:
                    product = Products(title=product, description=description, price=randrange(10,1000), stock=randint(2,100), store_owner=manager_user, approved=True, image=f'{product}{extension}', category_id=key+1)
                    db.session.add(product)


            db.session.commit()

            # Creating 10 orders for demonstration
            for _ in range(10):
                order_status = choice(['Pending', 'Transit', 'Delivered'])
                order_date = datetime.utcnow() - timedelta(days=randint(1, 30))
                order = Orders(customer=customer_user, status=order_status, created_at=order_date, updated_at=order_date)
                db.session.add(order)

                for _ in range(randint(1, 5)):
                    product = choice(Products.query.all())
                    quantity = randint(1, 10)
                    price_per_quantity = product.price
                    item = ItemsOrdered(item=product, quantity=quantity, price_per_quantity=price_per_quantity, order=order)
                    db.session.add(item)

            # Create cart items for customers
            for _ in range(5):
                product = choice(Products.query.all())
                quantity = randint(1, 10)
                cart_item = Cart(customer_id = customer_user.id, product=product, quantity=quantity)
                db.session.add(cart_item)

            # Creating 10 feedbacks for demonstration
            feedback_comments = ["Great product!", "Satisfactory", "Could be better", "I love this product!", "Not worth the price"]
            for _ in range(10):
                product = choice(Products.query.all())
                customer = choice(User.query.filter_by(role_id=1).all())
                rating = randint(1, 5)
                comment = choice(feedback_comments)
                feedback = Feedback(user_id=customer.id, product_id=product.id, rating=rating, review=comment)
                db.session.add(feedback)
                product.compute_average_rating()

            db.session.commit()

            print("Database tables created.")
        else:
            print("Database tables already exist.")
