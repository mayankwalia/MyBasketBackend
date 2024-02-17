from .instances import db
from datetime import datetime, timedelta

class User(db.Model):
    __tablename__ = 'User'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(70), nullable=False)

    # Address and other details provided by user during checkout
    delivery_details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # For tracking user activity and sending reminders
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # Monthly report type
    report_type = db.Column(db.Enum('HTML', 'PDF'), default='HTML', nullable=False)

    # For manager signup approved column is used 
    approved = db.Column(db.Boolean, nullable=False, default=False)
    # For deactivating account
    active = db.Column(db.Boolean, nullable=False, default=True)

    role_id = db.Column(db.Integer, db.ForeignKey('Role.id'), nullable=False, default=1)
    role = db.relationship('Role', backref='users', lazy='subquery')

    def update_last_activity(self):
        self.last_activity = datetime.utcnow()
        db.session.commit()


class Role(db.Model):
    __tablename__ = 'Role'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)

class Category(db.Model):
    __tablename__ = 'Category'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    approved = db.Column(db.Boolean, nullable=False, default=False)
    owner = db.relationship('User', foreign_keys=[owner_id], lazy='subquery')


class Feedback(db.Model):
    __tablename__ = 'Feedback'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    review = db.Column(db.Text)
    rating = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('Products.id'), nullable=False)
    user = db.relationship('User', backref='feedbacks_given', foreign_keys=[user_id], lazy='subquery')
    product = db.relationship('Products', backref='feedbacks', foreign_keys=[product_id], lazy='subquery')

class ManagerRequests(db.Model):
    __tablename__ = 'ManagerRequests'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    type = db.Column(db.Enum('Add Category', 'Update Category', 'Remove Category','Approve Manager'), nullable=False)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    # Stores category id or store owner id based on the request type
    relatedId = db.Column(db.Integer)
    approved = db.Column(db.Boolean, nullable=False, default=False)
    user = db.relationship('User', foreign_keys=[user_id], lazy='subquery')


class Products(db.Model):
    __tablename__ = 'Products'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    # Stores the image name (stored at static/images)
    image = db.Column(db.String(255))
    # Not used currently but can be used to approve products by admin (if needed)
    approved = db.Column(db.Boolean, nullable=False, default=False)
    # Controls whether the product is visible to customers
    visibility = db.Column(db.Boolean, nullable=False, default=True)
    discount = db.Column(db.Float, nullable=False, default=0)
    # Quantity of product available for sale (added by store manager while adding product)
    initialStock = db.Column(db.Integer, nullable=False, default=100)
    # Current stock (Still Remaining to be sold)
    stock = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.Enum('kg', 'lt', 'lbs','qty'), default='kg')
    manufacture_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expiry_date = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(days=365), nullable=False)
    # Aggregate rating of the product provided by customers
    average_rating = db.Column(db.Float, nullable=False, default=0)
    store_owner_id = db.Column(db.Integer, db.ForeignKey('User.id'),  nullable=False)
    category_id = db.Column(db.Integer,  db.ForeignKey('Category.id'), default = 1)
    store_owner = db.relationship('User', foreign_keys=[store_owner_id], lazy='subquery')
    category = db.relationship('Category', backref='products', lazy='subquery')

    
    def compute_average_rating(self):
        feedbacks = self.feedbacks
        if len(feedbacks) == 0:
            self.average_rating = 0
            return
        total = 0
        for feedback in feedbacks:
            total += feedback.rating
        self.average_rating = total/len(feedbacks)
        return


class Cart(db.Model):
    __tablename__ = 'Cart'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('Products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product = db.relationship('Products',foreign_keys=[product_id], lazy='subquery')

# Think it like a basket
class Orders(db.Model):
    __tablename__ = 'Orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    # Current status of the order: Can be changed by Store manager/ Admin or customer can cancel the order if it is not delivered
    status = db.Column(db.Enum('Transit', 'Delivered', 'Cancelled', 'Pending', 'Returned'), default='Transit', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    customer = db.relationship('User', backref='my_orders', foreign_keys=[customer_id], lazy='subquery')

class ItemsOrdered(db.Model):
    __tablename__ = 'ItemsOrdered'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('Orders.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('Products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_quantity = db.Column(db.Float, nullable=False)
    order = db.relationship('Orders', backref='items_ordered', lazy='subquery')
    item = db.relationship('Products', backref='orders_placed', lazy='subquery')