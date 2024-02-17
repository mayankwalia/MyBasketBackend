from application.instances import mail, app
from flask_mail import Message

def sendMail(RECEIVER_ADDRESS, SUBJECT, MESSAGE, ATTACHMENT=None, mime_type="application/pdf"):
    try:
        msg = Message(
            recipients=[RECEIVER_ADDRESS],
            sender=app.config['MAIL_USERNAME'],
            subject=SUBJECT
        )

        # Attach HTML content
        if mime_type == "text/html":
            msg.html = MESSAGE

        # Attachments
        if ATTACHMENT:
            with app.open_resource(ATTACHMENT) as fp:
                if mime_type == "application/pdf":
                    msg.attach(f"{RECEIVER_ADDRESS}_report.pdf", mime_type, fp.read())
                elif mime_type == "application/x-zip":
                    msg.attach(f"{RECEIVER_ADDRESS}_exported.zip", mime_type, fp.read())
                elif mime_type == "text/csv":
                    msg.attach(f"{RECEIVER_ADDRESS}_data.csv", mime_type, fp.read())

        mail.send(msg)
        return True
    except Exception as e:
        print("Error", e)
        return False