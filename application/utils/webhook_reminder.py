from json import dumps
from httplib2 import Http
import os
from dotenv import load_dotenv

load_dotenv(".env")

def google_chat_reminder(users):
    try: 
        url = os.getenv('GOOGLE_CHAT_WEBHOOK_URL')
        for user in users:
            app_message = {
'text': f"""Hi {user.username}, 
We hope you're doing well! We've noticed that you haven't placed any orders in our app in the last 24 hours. We have a wide selection of fresh products and exciting deals waiting for you. Don't miss out!
Remember, we're here to make your shopping experience easy and convenient. Visit us today and let's make your next shopping trip a great one!

Best regards,
The MyBasket Team
"""
                }
            message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
            http_obj = Http()
            response = http_obj.request(
                uri=url,
                method='POST',
                headers=message_headers,
                body=dumps(app_message),
            )
        return True
    except Exception as e:
        print("Error",e)
        return False