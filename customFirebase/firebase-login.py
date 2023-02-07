import pyrebase
import json

config = json.load(open('firebase/loginConfig.json'))
firebase = pyrebase.initialize_app(config)

auth = firebase.auth()

def signup(email,password) :
    email = "abcdefgh@gmail.com"
    password = "abcdefgh"
    auth.create_user_with_email_and_password(email,password)
    
def login(email,password) :
    acc = auth.sign_in_with_email_and_password(email,password)
    
    #printing account info
    print(auth.get_account_info(acc['idToken']))
       
def main() :
#    signup()
    login()

if __name__ == '__main__':
    main()