import logging
from celery import shared_task
from application.models import User, Orders
from jinja2 import Template
from weasyprint import HTML
import uuid
import os
from datetime import datetime, timedelta

logging.basicConfig(filename='logs/tasks.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

def getUserToRemind(notPurchasedToday = False):
    last_24_hours = datetime.now() - timedelta(hours=24)
    try:
        # Role Id = 1 for customers
        if not notPurchasedToday:
            users = User.query.filter(User.role_id == 1, User.last_activity <= last_24_hours).all()
            logging.info(f'Users to send daily reminder for not visiting the app today: {users}')
            return users
        else:
            orders = Orders.query.filter(Orders.created_at >= last_24_hours).all()
            user_ids = [order.customer_id for order in orders]
            users = User.query.filter(User.role_id == 1, ~User.id.in_(user_ids)).all()
            logging.info(f'Users to send daily reminder for not purchasing today: {users}')
            return users
    except Exception as e:
        logging.info(f'Error in getting users: {e}')
        return None

@shared_task()
def remainder_emails():
    from application.utils.mail import sendMail
    try:
        not_visited_users = getUserToRemind()
        for user in not_visited_users:
            data = {'username': user.username, 'email': user.email}
            message = formatMessage(data, template='visitReminder')
            response = sendMail(data['email'],"Daily Reminder for visiting MyBasket Store",message, ATTACHMENT=None, mime_type="text/html")
            logging.info('Successfully sent visit remainder emails')
        not_purchased_users = getUserToRemind(notPurchasedToday=True)
        for user in not_purchased_users:
            data = {'username': user.username, 'email': user.email}
            message = formatMessage(data, template='purchaseReminder')
            response = sendMail(data['email'],"Daily Reminder for purchasing at MyBasket Store",message, ATTACHMENT=None, mime_type="text/html")
            logging.info('Successfully sent purchase remainder emails')
        return 'Successfully Sent'
    except Exception as e:
        logging.info(f'Error in getting users: {e}')
        return 'Failed to send'

@shared_task(ignore_result=False)
def reminder_google_chat():
    from application.utils.webhook_reminder import google_chat_reminder
    not_visited_users = getUserToRemind()
    response = google_chat_reminder(not_visited_users)
    if(response): return 'Successfully Sent'
    else : return 'Failed to send'


def formatMessage(data, template='visitReminder'):
    template_path = os.path.join(os.path.dirname(__file__), 'templates', f'{template}.html')
    with open(template_path, 'r') as message_template:
        template_content = message_template.read()
        template = Template(template_content)
        message = template.render(data=data)
    return message


@shared_task(shared_task(ignore_result=False))
def monthlyReport():
    from application.models import User, Orders, ItemsOrdered
    users = User.query.filter_by(role_id = 1).all()
    today = datetime.now()
    starting_date = today - timedelta(days=30)
    try:
        # Loop over all the users and send them the report
        for user in users:
            orders = Orders.query.filter(Orders.customer_id == user.id, Orders.created_at >= starting_date).all()
            data = {}
            data['orders']=[]
            data['username'] = user.username
            data['email'] = user.email
            data['month'] = today.strftime("%B")
            totalExpenditure = 0

            if len(orders) == 0:
                continue
            for order in orders:
                order_dict = {}
                items = order.items_ordered
                order_dict['id'] = order.id
                order_dict['status'] = order.status
                order_dict['created_at'] = order.created_at.strftime("%d %B %Y")
                order_dict['items'] = []
                orderTotal = 0
                for item in items:
                    item_dict = {}
                    item_dict['title'] = item.item.title
                    item_dict['quantity'] = item.quantity
                    item_dict['price'] = item.price_per_quantity.__round__(2)
                    order_dict['items'].append(item_dict)
                    orderTotal += item.price_per_quantity*item.quantity
                order_dict['total'] = orderTotal.__round__(2)
                if order.status != 'Cancelled' and order.status != 'Returned':
                    totalExpenditure += orderTotal
                data['orders'].append(order_dict)
            data['totalExpenditure'] = totalExpenditure.__round__(2)
            print(data)
            if data['orders'] == [{}] or data['orders'] == []:
                data['orders'] = None
            from application.utils.mail import sendMail
            if user.report_type == 'HTML':
                message = formatMessage(data,'monthlyReport')
                sendMail(user.email, 'Monthly HTML Report', message, mime_type='text/html')
            else:
                file = create_pdf(data)
                if(file):
                    sendMail(user.email, 'Monthly PDF Report', 'Please find the attached Monthly Report', ATTACHMENT=file, mime_type='application/pdf')
                else:
                    os.remove(os.path.join(os.path.dirname(__file__), 'static/PDF', file))
        return True
    except Exception as e:
        print(e)
        return False


# It takes a template file and data and returns the formatted message
def format_report(template_file, data=[]):
    template_path =os.path.join(os.path.dirname(__file__), 'templates', template_file)
    try:
        with open(template_path, 'r') as file_:
            template = Template(file_.read())
            return template.render(data=data)
    except FileNotFoundError:
        print(f"Error: File '{template_path}' not found.")
        return None

# It creates a PDF file and returns the filename
def create_pdf(data):
    message = format_report('monthlyReport.html',data)
    html = HTML(string=message)
    file_name = os.path.join(os.path.dirname(__file__), 'static/PDF', str(uuid.uuid4())+'.pdf')
    html.write_pdf(target=file_name)
    return file_name
