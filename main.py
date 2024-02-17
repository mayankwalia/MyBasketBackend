from application import create_app
from application.api import LoginAPI, SignupAPI, ProductsAPI, CategoriesAPI, UsersAPI, FeedbackAPI, ManagerRequestsAPI, TestAPI 
import logging
logging.basicConfig(filename='logs/debug.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

app = None
api = None
celery = None
app, jwt, api, celery = create_app()


handler = logging.StreamHandler()
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)


import redis
from application.models import User
from flask_jwt_extended import get_jwt, jwt_required

@jwt.user_lookup_loader
def user_loader(jwt_header, jwt_payload):
    identity = jwt_payload["sub"]
    # Load the user based on the provided identity
    user = User.query.filter_by(username=identity).first()
    if user:
        return user
    return None

# Setup redis connection for storing the blocklisted tokens.
jwt_redis_blocklist = redis.StrictRedis(
    host="localhost", port=6379, db=0, decode_responses=True
)

# Callback function to check if a JWT exists in the redis blocklist
@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
    jti = jwt_payload["jti"]
    token_in_redis = jwt_redis_blocklist.get(jti)
    return token_in_redis is not None

# Endpoint for revoking the current users access token. Save the JWTs unique
# identifier (jti) in redis. Also set a Time to Live (TTL)  when storing the JWT
# so that it will automatically be cleared out of redis after the token expires.
@app.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    jwt_redis_blocklist.set(jti, "", ex=timedelta(hours=24))
    return jsonify(msg="Access token revoked")


########## Exporting data to CSV (User Triggered async job) #########
import csv    
from flask import send_file
@celery.task(name="generate_csv")
def generate_csv(managerId):
    try:
        manager = User.query.filter_by(id=managerId).first()
        products = Products.query.filter_by(store_owner_id=managerId).all()
        csv_data = {}
        for product in products:
            csv_data[product.id] = {
                'ID': product.id,
                'Title': product.title,
                'Description': product.description,
                'MRP': product.price,
                'Discount %': product.discount,
                'Discounted Price': product.price * (1 - product.discount / 100),
                'Unit (measured in)': product.unit,
                'Initial Stock': product.initialStock,
                'Stock Left': product.stock,
                'Items Sold': product.initialStock - product.stock,
                'Manufacture Date': product.manufacture_date,
                'Expiry Date': product.expiry_date,
                'Category': product.category.name,
                'Average Rating': 'No ratings yet' if product.average_rating == 0.0 else product.average_rating,
                'Visibility to customers (Ask admin for toggling this on/off)': 'Yes' if product.visibility else 'No',
            }
        file_path = 'application/static/csv'
        filename = 'data'
        with open(f'{file_path}/{filename}.csv', "w") as file:
            myWriter = csv.writer(file)
            headerRow = True
            for row in csv_data.values():
                if headerRow:
                    myWriter.writerow(row.keys())
                    headerRow = False
                myWriter.writerow(row.values())
            file.close()
        return True
    except Exception as e:
        print("Error",e)
        return False

@app.route('/export-data/<int:managerId>', methods=['GET'])
@jwt_required()
def export_data(managerId):
    res = generate_csv.delay(managerId)
    if res:
        return jsonify({'message':'CSV generation request is in progress',
                "taskId": res.id,
                "state": res.state,
                "result": res.result})
    else:
        return {'message': 'Something went wrong'}, 500

@app.route("/check-export-status/<task_id>")
def check_csv_status(task_id):
    task = generate_csv.AsyncResult(task_id)
    if task.state == 'SUCCESS':
        return send_file('static/csv/data.csv', as_attachment=True, download_name='exported_data.csv'),200
    elif task.state in ['PENDING', 'PROGRESS']:
        return {'status': task.state}, 202
    else:
        return {'message': 'CSV generation failed or in an unknown state'}, 500


####### Registering the API endpoints #######
api.add_resource(TestAPI, '/test')
api.add_resource(LoginAPI, '/login')
api.add_resource(SignupAPI, '/signup')
api.add_resource(UsersAPI, '/users', '/users/<int:user_id>')
api.add_resource(ProductsAPI, '/products', '/products/<int:product_id>')
api.add_resource(CategoriesAPI, '/categories', '/categories/<int:category_id>')
api.add_resource(FeedbackAPI, '/review', '/review/<int:feedback_id>')
api.add_resource(ManagerRequestsAPI, '/requests', '/requests/<int:request_id>')

from application.controllers import *
from application.tasks import remainder_emails, reminder_google_chat, monthlyReport


if __name__ == '__main__':
    app.run()
