import string
import random

import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from base64 import urlsafe_b64decode, urlsafe_b64encode
from email.mime.text import MIMEText

SCOPES = ['https://mail.google.com/']
our_email = 'kalamarisharing@gmail.com'

def id_generator() :
    n = 6
    chars= string.ascii_uppercase + string.ascii_lowercase + string.digits
    
    generated = ''
    generated = generated.join(random.choice(chars) for _ in range(n))
    
    return generated

def gmail_authenticate():
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists("customPy/token.pickle"):
        with open("customPy/token.pickle", "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('customPy/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open("customPy/token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

# get the Gmail API service

def build_message(destination, obj, body):
    message = MIMEText(body)
    message['to'] = destination
    message['from'] = our_email
    message['subject'] = obj
    return {'raw': urlsafe_b64encode(message.as_bytes()).decode()}

def send_message(service, destination, obj, body):
    return service.users().messages().send(userId="me", body=build_message(destination, obj, body)).execute()

def sendMailtoThis(email,otp) :
    service = gmail_authenticate()
    send_message(service, email, "Your OTP for kalamari", "This is your OTP " + otp)

#to test purpose
def main() :
#    sendMailtoThis("kalamarisharing@gmail.com", id_generator())
    gmail_authenticate()

if __name__ == "__main__":
    main()
