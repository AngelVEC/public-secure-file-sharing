#custom python code
import os
import customPy.splitting as splitting
import customPy.joining as joining
import customFirebase.firestore as fs
import customPy.basic as basic
import customPy.zip as zippingFile

#python libraries
from flask_dropzone import Dropzone
import pyrebase
import json
from flask import Flask, render_template, request, redirect, url_for, session,flash,send_file
import re
from datetime import datetime, timezone
import humanize

app = Flask(__name__)

app.jinja_env.filters['zip'] = zip

# Config the dropzone
app.config['DROPZONE_ALLOWED_FILE_CUSTOM'] = True
app.config['DROPZONE_ALLOWED_FILE_TYPE'] = 'image/*, .pdf, .txt, .mp4, .py, .zip, .7z'
app.config['DROPZONE_MAX_FILE_SIZE'] = 30000 


# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'Insert your key here'

#initialize firebase
config = json.load(open('customFirebase/loginConfig.json'))
firebase = pyrebase.initialize_app(config)

auth = firebase.auth()

# =================================== Routing error handling ===============================================
@app.errorhandler(404) 
def pageNotFound(e) :
    return redirect(url_for('index'))
    
@app.errorhandler(500)
def InternalServerError(e) :
    if 'fileID' in session :
        session.pop('fileID', default=None)
    if 'owner' in session :
        session.pop('owner', default=None)
    flash("you trying to open a something that you should't, did you?", "failedCode")
    return redirect(url_for('index'))

# =================================== Start Page ===========================================================

# http://localhost:5000/ start page
@app.route('/')
def index() :
    if 'loggedin' in session :
        return redirect(url_for('home'))
    
    return render_template ('index.html')

# ====================================== LOGIN =============================================================

#if user already login before(cookie still stored), it will redirecty instantly to user dashboard
@app.route('/login')
def openLoginPage() :
    #check if user session still in the browser (cookies that they are logged in)
    if 'loggedin' in session:
        return redirect(url_for('home'))
    
    return render_template ('login.html')

'''
# http://localhost:5000/login - the following will be our login page, which will use both GET and POST requests
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'e-mail' in request.form and 'password' in request.form:
        # Create variables for easy access
        e_mail = str.lower(request.form['e-mail'])
        password = request.form['password']
         
        # If account exists in accounts table in out database
        if e_mail and password:
            try :
                auth.sign_in_with_email_and_password(e_mail,password)
            except :
                flash('Incorect e-mail/Password!','failed2')
                return redirect(url_for('login'))
            
            #find the username from firestore
            userName = fs.getUserNameFromEmail(e_mail)
            result = fs.accountInformation(userName)
            
            # Create session data, we can access this data in other routes
            
            session['loggedin'] = True
            session['username'] = userName
            session['email'] = e_mail
            session['role'] = result['role']
            
            # Redirect to home page
            return redirect(url_for('home'))
        
    return redirect(url_for('login'))
'''

# http://localhost:5000/login - the following will be our login page, which will use both GET and POST requests
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'e-mail' in request.form and 'password' in request.form:
        # Create variables for easy access
        e_mail = str.lower(request.form['e-mail'])
        password = request.form['password']
            
        # If account exists in accounts table in out database
        if e_mail and password:
            try :
                auth.sign_in_with_email_and_password(e_mail,password)
            except :
                flash('Incorect e-mail/Password!','failed2')
                return redirect(url_for('login'))
            
            #find the username from firestore
            userName = fs.getUserNameFromEmail(e_mail)
            result = fs.accountInformation(userName)
            
            # Create session data, we can access this data in other routes
            session['username'] = userName
            session['email'] = e_mail
            session['role'] = result['role']
            
            if session['role'] == 'admin' :
                session['loggedin'] = True
                return redirect(url_for('home'))
            
            #if the one login is user
            else :
                twoFactor = basic.id_generator()
            
                session['twoFactor'] = twoFactor
                
                #send the email before redirect to authenticate page
                basic.sendMailtoThis(e_mail,twoFactor)
                
                # Redirect to authenticate page
                return redirect(url_for('authenticate'))
            

@app.route('/authenticate')
def authenticate() :
    if 'twoFactor' in session :
        return render_template('2fa.html')
    
    return redirect(url_for('login'))

@app.route('/authenticate', methods=['GET', 'POST'])
def getAuthenticate() :
    if request.method == 'POST' :
        userInput = request.form['2FA']
        twoFactor = session['twoFactor']
        
        if userInput == twoFactor :
            session.pop('twoFactor', default=None)
            session['loggedin'] = True
            return redirect(url_for('home'))
        
        else :
            session.pop('twoFactor', default=None)
            session.pop('username', default=None)
            session.pop('email', default=None)
            session.pop('role', default=None)
            flash("wrong 2FA, please try again!!!","failed2")
            return redirect(url_for('home'))

# ============================================== Register =====================================================
#if user already login before(cookie still stored), it will redirecty instantly to user dashboard
@app.route('/register')
def openRegisterPage() :
    if 'loggedin' in session:
        return redirect(url_for('home'))
    return render_template ('register.html')
    
# http://localhost:5000/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    msg2 = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = str.lower(request.form['username'])
        password = request.form['password']
        email = str.lower(request.form['email'])
        
        # do a validation check
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
            return render_template('register.html', msg=msg)
        
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
            return render_template('register.html', msg=msg)
        
        elif not re.fullmatch(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#\$%\^&\*\+\-]).{8,}$', password):
            print(password)
            msg= 'Password should be at least 8 characters and contain at least a capital letter,small letter,number and special character'
            return render_template('register.html', msg=msg)
        
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
            return render_template('register.html', msg=msg)
        
        #checking if userName already used or not

        if fs.userNameCheckIfExist(username) == True :
            msg = "user name has been used"
            return render_template('register.html', msg=msg)
                
        #inserting account info to the firebase auth
        try :
            auth.create_user_with_email_and_password(email,password)
        except :
            msg = "email has been used"
            return render_template('register.html', msg=msg)
        
        #inserting userName information to the firestore database
        
        fs.addNewAccount(email,username)
        
        msg2 = "Account created"
            
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg2=msg2)

#========================================= Logout =====================================================================

# http://localhost:5000/logout - this will be the logout page
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   session.pop('role', None)
   # Redirect to login page
   return redirect(url_for('index'))

#=========================================== Dashboard (user/admin) ================================================================
# http://localhost:5000/home - this will be the dashboard page, only accessible for loggedin users
@app.route('/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        #check that user who login, is with right role
        theRole = session['role']
        theUser = session['username']
        theInfo = fs.accountInformation(theUser)
        #if found out that it's different role than what it should be, will be forced to log out
        if theRole != theInfo['role'] :
            return redirect(url_for('logout'))
        
        if session['role'] == "admin" :
            # admin is loggedin show the admin page
            #getting the list of database available
            instance_list = splitting.allInstanceList("Database")
            
            #getting the list of database backup
            backup_instance_list = splitting.allInstanceList("Backup")

            counter_main = 0
            counter_bkp = 0

            try :
                instance_volume = splitting.getVolume(instance_list)
                
                for i in instance_list :

                    if i['Instance_state'] == "running" :
                        i['usedVolume'] = instance_volume[counter_main]
                        counter_main = counter_main + 1
            except :
                pass
            
            try :
                bkp_volume = splitting.getVolume(backup_instance_list)
                
                for i in backup_instance_list :
                    if i['Instance_state'] == "running" :
                        i['usedVolume'] = bkp_volume[counter_bkp]
                        counter_bkp = counter_bkp + 1
            except :
                pass
                
            
            return render_template('adminPage.html', username=session['username'], instance_list=instance_list, backup_instance_list=backup_instance_list,counter_main=counter_main,counter_bkp=counter_bkp)
        elif session['role'] == "user":
            # User is loggedin show them the home page
            accountName = session['username']
            result = fs.getallFileinfo(accountName)
            
            allResult = fs.getAlltheListofSharedFile(accountName)
            sharedFile = []
            
            for i in allResult :
                codeInfo = fs.getCodesInfo(i['code'])
                sharedFile.append(codeInfo)
            
            fileName = []
            passwordProtected = []
            for i in sharedFile :
                data = fs.getInfoBasedOnId(i['owner'],i['fileID'])
                fileName.append(data['fileName'])
                passwordProtected.append(data['havePassword'])
                    
            return render_template('home.html',username=session['username'] ,result = result,sharedFile = sharedFile, fileName = fileName, passwordProtected = passwordProtected)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

#this is for sysadmin (turn on and off instances) in their dashboard
@app.route('/home', methods=['GET', 'POST'])
def homeFunction() :
    if request.method == 'POST' and session['role'] == "user" :
        if request.form['action'] == "Download" :
            originalName = request.form['originalName']
            fileID = request.form['file_id']
            accountName = session['username']
            
            #get the file info from firebase
            fileInfo = fs.getInfoBasedOnId(accountName,fileID)
            
            #get the list available database that is running and on firebase database list
            splitMainDatabase = fileInfo['mainDatabase'].split(",")
            
            instance_list = splitting.allInstanceList("Database")
            
            mainDatabase = []
            for i in splitMainDatabase :
                for k in instance_list:
                    if k.get('Instance_state') == 'running' and i in k.get('Instance_name') :
                        mainDatabase.append(k)
            
            #get the list available of bkp database that is running and on firebase bkp database list
            splitBkpDatabase = fileInfo['bkpDatabase'].split(",")
            
            backup_instance_list = splitting.databaseInstanceList("Backup")
            
            bkpDatabase = []
            for i in splitBkpDatabase :
                for k in backup_instance_list :
                    if k.get('Instance_state') == 'running' and i in k.get('Instance_name') :
                        bkpDatabase.append(k)
            
            file_download = joining.joinAndDecrypt(accountName,fileID,originalName,mainDatabase,bkpDatabase)
            return send_file(file_download, as_attachment=True)
        
        elif request.form['action'] == "Download Shared File" :
            originalName = request.form['fileName']
            fileID = request.form['file_id']
            accountName = request.form['owner']
            
            #this code is a checker to make sure only the right user that can access (if got shared)
            try :
                #get file information of the owner
                result = fs.getInfoBasedOnId(accountName,fileID)
                if result["shared"] == True :
                    shareCode = result["shareCode"]
                    
                    result2 = fs.getCodesInfo(shareCode)
                    
                    sharedPeople = result2["sharePeople"]
                    
                    #current account Access
                    emailUser = session["email"]
                    
                    if emailUser in sharedPeople :
                        pass
                    else :
                        flash("you trying to download a file without permission", "failedCode")
                        return redirect(url_for("home"))
                    
                else :
                    flash("you trying to download a file without permission", "failedCode")
                    return redirect(url_for("home"))
            except :
                pass
            
            #get the file info from firebase
            fileInfo = fs.getInfoBasedOnId(accountName,fileID)
            
            #get the list available database that is running and on firebase database list
            splitMainDatabase = fileInfo['mainDatabase'].split(",")
            
            instance_list = splitting.allInstanceList("Database")
            
            mainDatabase = []
            for i in splitMainDatabase :
                for k in instance_list:
                    if k.get('Instance_state') == 'running' and i in k.get('Instance_name') :
                        mainDatabase.append(k)
            
            #get the list available of bkp database that is running and on firebase bkp database list
            splitBkpDatabase = fileInfo['bkpDatabase'].split(",")
            
            backup_instance_list = splitting.databaseInstanceList("Backup")
            
            bkpDatabase = []
            for i in splitBkpDatabase :
                for k in backup_instance_list :
                    if k.get('Instance_state') == 'running' and i in k.get('Instance_name') :
                        bkpDatabase.append(k)
            
            if not mainDatabase and not bkpDatabase :
                flash("Server are under maintenance", "failedCode")
                return redirect(url_for('home'))
                
            file_download = joining.joinAndDecrypt(accountName,fileID,originalName,mainDatabase,bkpDatabase)
            return send_file(file_download, as_attachment=True)
        
        elif request.form['action'] == "File description": 
            #add it to session before redirect to the page
            fileID = request.form['file_id']
            session['fileID'] = fileID
            return redirect(url_for('fileInfo'))
        
        elif request.form['action'] == "Shared File Desc" :
            #add it to session before redirect to the page
            fileID = request.form['file_id']
            owner = request.form['owner']
            
            #this code is a checker to make sure only the right user that can access (if got shared)
            try :
                #get file information of the owner
                result = fs.getInfoBasedOnId(owner,fileID)
                if result["shared"] == True :
                    shareCode = result["shareCode"]
                    
                    result2 = fs.getCodesInfo(shareCode)
                    
                    sharedPeople = result2["sharePeople"]
                    
                    #current account Access
                    emailUser = session["email"]
                    
                    if emailUser in sharedPeople :
                        pass
                    else :
                        flash("you trying to access a file without permission", "failedCode")
                        return redirect(url_for("home"))
                    
                else :
                    flash("you trying to access a file without permission", "failedCode")
                    return redirect(url_for("home"))
            except :
                pass
            
            
            session['fileID'] = fileID
            session['owner'] = owner
            return redirect(url_for('fileInfo'))
        
        #new Line
        elif request.form['action'] == "Shared downloadPass":
            originalName = request.form['file_modalFileName2']
            fileID = request.form['file_modalID2']
            accountName = request.form['file_modalOwner2']
            password = request.form['passwordInput']
            
            current = os.getcwd()
            
            #this code is a checker to make sure only the right user that can access (if got shared)
            try :
                #get file information of the owner
                result = fs.getInfoBasedOnId(accountName,fileID)
                if result["shared"] == True :
                    shareCode = result["shareCode"]
                    
                    result2 = fs.getCodesInfo(shareCode)
                    
                    sharedPeople = result2["sharePeople"]
                    
                    #current account Access
                    emailUser = session["email"]
                    
                    if emailUser in sharedPeople :
                        pass
                    else :
                        flash("you trying to download a file without permission", "failedCode")
                        return redirect(url_for("home"))
                    
                else :
                    flash("you trying to download a file without permission", "failedCode")
                    return redirect(url_for("home"))
            except :
                pass
            
            #get the file info from firebase
            fileInfo = fs.getInfoBasedOnId(accountName,fileID)
            
            #get the list available database that is running and on firebase database list
            splitMainDatabase = fileInfo['mainDatabase'].split(",")
            
            instance_list = splitting.allInstanceList("Database")
            
            mainDatabase = []
            for i in splitMainDatabase :
                for k in instance_list:
                    if k.get('Instance_state') == 'running' and i in k.get('Instance_name') :
                        mainDatabase.append(k)
            
            #get the list available of bkp database that is running and on firebase bkp database list
            splitBkpDatabase = fileInfo['bkpDatabase'].split(",")
            
            backup_instance_list = splitting.databaseInstanceList("Backup")
            
            bkpDatabase = []
            for i in splitBkpDatabase :
                for k in backup_instance_list :
                    if k.get('Instance_state') == 'running' and i in k.get('Instance_name') :
                        bkpDatabase.append(k)
            
            file_download = joining.joinWithPassword(accountName,fileID,originalName,mainDatabase,bkpDatabase)
            
            path = f"./sendUser/{accountName}/{fileID}/"
            
            #make the directory so you can unzip it to the folder
            splitting.auto_directory(path)
            
            #unzip it with password
            try :
                zippingFile.unZipFile2(file_download,password,path)
            except:
                flash("wrong password", "failedCode2")
                return redirect(url_for('home'))
            
            #go back to old directory, instead of the new one (because of pyminizip)
            os.chdir(current)
            
            return send_file(f"{path}{originalName}", as_attachment=True)
        
            #print(originalName,fileID,accountName,password)
            
        elif request.form['action'] == "downloadPass":
            originalName = request.form['file_modalFileName']
            fileID = request.form['file_modalID']
            accountName = session['username']
            password = request.form['passwordInput']
            
            current = os.getcwd()
            
            print(fileID)
            #get the file info from firebase
            fileInfo = fs.getInfoBasedOnId(accountName,fileID)
            
            #get the list available database that is running and on firebase database list
            splitMainDatabase = fileInfo['mainDatabase'].split(",")
            
            instance_list = splitting.allInstanceList("Database")
            
            mainDatabase = []
            for i in splitMainDatabase :
                for k in instance_list:
                    if k.get('Instance_state') == 'running' and i in k.get('Instance_name') :
                        mainDatabase.append(k)
            
            #get the list available of bkp database that is running and on firebase bkp database list
            splitBkpDatabase = fileInfo['bkpDatabase'].split(",")
            
            backup_instance_list = splitting.databaseInstanceList("Backup")
            
            bkpDatabase = []
            for i in splitBkpDatabase :
                for k in backup_instance_list :
                    if k.get('Instance_state') == 'running' and i in k.get('Instance_name') :
                        bkpDatabase.append(k)
            
            file_download = joining.joinWithPassword(accountName,fileID,originalName,mainDatabase,bkpDatabase)
            
            path = f"./sendUser/{accountName}/{fileID}/"
            
            #make the directory so you can unzip it to the folder
            splitting.auto_directory(path)
            
            #unzip it with password
            try :
                zippingFile.unZipFile2(file_download,password,path)
            except:
                flash("wrong password", "failedCode2")
                return redirect(url_for('home'))
            
            #go back to old directory, instead of the new one (because of pyminizip)
            os.chdir(current)
            
            return send_file(f"{path}{originalName}", as_attachment=True)
        
        elif request.form['action'] == "DeleteFile" :
            #add it to session before redirect to the page
            fileID = request.form['file_deleteModalid']
            accountName = session['username']
            
            #get the file info from firebase
            fileInfo = fs.getInfoBasedOnId(accountName,fileID)            
            
            #remove people from the shared if any
            try :
                code = fileInfo['shareCode']
                #get the list of people that been shared
                codeResult = fs.getCodesInfo(code)
                sharePeople = codeResult['sharePeople']
                
                #get the account name based on list of sharePeople(email)
                accountNameList = []
                
                for i in sharePeople :
                    accountName = fs.getUserNameFromEmail(i)
                    accountNameList.append(accountName)

                #first step delete the code from accountNameList (under account database)
                for accountName in accountNameList :
                    fs.deleteSharedCodeFromAccount(accountName,code)
                    
                #second step delete the code from sharedCode databsae
                fs.deleteCodefromSharedDatabase(code)
            except :
                pass
            
            try :
                #third step revoke the sharing from database
                fs.revokeShared(accountName,fileID)
            except :
                pass

            #fourth step deleting the actual file from firestore database
            fs.deleteFileFromDatabase(accountName,fileID)
            flash('File successfully deleted', 'success')
            
        
    elif request.method == 'POST' and 'Instance_ID' in request.form and 'Instance_state' in request.form :
        instance_state = request.form['Instance_state']
        instance_ID = request.form['Instance_ID']
        if instance_state == "running" :
            splitting.stopInstance(instance_ID)
        elif instance_state == "stopped" :
            splitting.startInstance(instance_ID)
        
    return redirect(url_for('home'))

#to add file by code to the user

@app.route('/code', methods =['GET' , 'POST'])
def code() :
    if request.method == 'POST' :
        code = request.form['code']
        email = session['email']
        accountName = session['username']

        #get the owner of the file
        fileInfo = fs.getCodesInfo(code)
        try :
            owner = fileInfo['owner']
        except :
            flash("Invalid Code", "failedCode")
            return redirect(url_for('home'))
                
        if owner == accountName :
            flash("You can't add yourself to your own file share", "failedCode")
        else :
            sharePeople = fileInfo['sharePeople']
            if email in sharePeople :
                flash("You are already inside the Shared List", "failedCode")
            else :
                sharePeople.append(email)
                
                #update the shared list of people on (sharedCode)
                fs.updateShared(code,fileInfo)
                
                #update the shared file to the account
                fs.addtoSharedFile(accountName,code)
                
                flash("Added to the shared list", "success")
        
    return redirect(url_for('home'))

#======================================== Profile Page =================================================================

# http://localhost:5000/profile - this will be the profile page, only accessible for loggedin users
@app.route('/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        e_mail = session['email']
        userName = session['username']
        # Show the profile page with account info
        return render_template('profile.html', e_mail = e_mail, userName = userName)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

#to change user Email on profile page
@app.route('/changeEmail', methods =['GET' , 'POST'])
def changeEmail() :
    if request.method == 'POST' :
        oldEmail = session['email']
        newEmail = request.form['e_mail']
        accountName = session['username']

        emailExist = fs.doesEmailExist(newEmail)
        if emailExist:
            flash("Email exists in database", "failed")
            return redirect(url_for('profile'))
        elif oldEmail == newEmail :
            flash("Please write new E-mail", "failed")
            return redirect(url_for('profile'))
        else :
            #change the email to the firebase authentication
            fs.changeEmail(oldEmail,newEmail)
            
            #change the email to the firestore database
            fs.changeDatabaseEmail(accountName,newEmail)
            
            #change the email to the session
            session['email'] = newEmail
            flash("Email changed", "success")
            
    return redirect(url_for('profile'))

#to send an email to user pn profile page
@app.route('/changePass', methods =['GET' , 'POST'])
def changePass() :
    email = session['email']
    auth.send_password_reset_email(email)
    flash("Please check your inbox or spam to change the password", "success")
    return redirect(url_for('profile'))

#===================================== Upload ============================================================

#to make sure only logged in user can access this
@app.route('/upload')
def upload():
    # Check if user is loggedin
    if 'loggedin' in session :
        return render_template('upload.html')
    return redirect(url_for('login'))

#upload file code
dropzone = Dropzone(app)
@app.route('/upload', methods =['GET', 'POST'])
def uploadfile() :
    
    #getting the list of database available
    instance_list = splitting.databaseInstanceList("Database")
    
    #getting the list of database backup
    backup_instance_list = splitting.databaseInstanceList("Backup")
    
    #concanate the instance and bkp instance number
    InstanceNumber = ""
    for i in instance_list :
        
        splitIt = i['Instance_name'].split("Database")
        if i == instance_list[-1]:        
            InstanceNumber = f'{InstanceNumber + splitIt[1]}'
        else :
            InstanceNumber = f'{InstanceNumber + splitIt[1]},'
    
    bkpInstanceNumber = ""
    for i in backup_instance_list :
        splitIt = i['Instance_name'].split("Backup")
        if i == backup_instance_list[-1]: 
            bkpInstanceNumber = f'{bkpInstanceNumber + splitIt[1]}'
        else :
            bkpInstanceNumber = f'{bkpInstanceNumber + splitIt[1]},'

    #initialize the account name
    accountName = session['username']
    
    #initialize the id for the file
    accountInfo = fs.accountInformation(accountName)
    totalCurrentFile = accountInfo['fileAdded']
    u_id = totalCurrentFile + 1
        
    if (len(instance_list) < 3 or len(backup_instance_list) < 3) :
        flash("Database Server is under maintenance, Please wait until the problem resolved", "databaseError")
        #this does absolute nothing, just to make sure the page refreshed after upload
        return redirect(url_for('loading'))
    
    if (len(instance_list) >= 3 and len(backup_instance_list) >= 3) :
        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            uploaded_file.save(uploaded_file.filename)

            #get the file size of uploaded file
            fileSize = os.stat(uploaded_file.filename).st_size
            fileSize = humanize.naturalsize(fileSize)
            
            splitting.encrypt(uploaded_file.filename,accountName,u_id)
            
            fs.addNewFileToUser(accountName,uploaded_file.filename,InstanceNumber,bkpInstanceNumber,fileSize)
        
        flash("File successfully Uploaded", "successUpload")
        #this does absolute nothing, just to make sure the page refreshed after upload
        return redirect(url_for('loading'))
    
    return redirect(render_template("home.html"))    

#to render loading page
@app.route('/loading')
def loading() :
    return render_template('extra/loading.html')

# ======================================== File uploaded / shared page ==========================================================

# http://localhost:5000/file - to see all the files that uploaded and shared
@app.route('/file')
def file() :
    if 'loggedin' in session :
        return redirect(url_for('home'))
    # if 'loggedin' in session :
    #     accountName = session['username']
    #     result = fs.getallFileinfo(accountName)
        
    #     allResult = fs.getAlltheListofSharedFile(accountName)
    #     sharedFile = []
        
    #     for i in allResult :
    #         codeInfo = fs.getCodesInfo(i['code'])
    #         sharedFile.append(codeInfo)
        
    #     fileName = []
    #     for i in sharedFile :
    #         data = fs.getInfoBasedOnId(i['owner'],i['fileID'])
    #         fileName.append(data['fileName'])
                   
    #     return render_template('file.html',result = result,sharedFile = sharedFile, fileName = fileName)
    return redirect(url_for('login'))

# file post method
@app.route('/file', methods=['GET', 'POST'])
def downloadFile() :
    # if request.method == 'POST' :
    #     if request.form['action'] == "Download" :
    #         originalName = request.form['originalName']
    #         fileID = request.form['file_id']
    #         accountName = session['username']
            
    #         #get the file info from firebase
    #         fileInfo = fs.getInfoBasedOnId(accountName,fileID)
            
    #         #get the list available database that is running and on firebase database list
    #         splitMainDatabase = fileInfo['mainDatabase'].split(",")
            
    #         instance_list = splitting.allInstanceList("Database")
            
    #         mainDatabase = []
    #         for i in splitMainDatabase :
    #             for k in instance_list:
    #                 if k.get('Instance_state') == 'running' and i in k.get('Instance_name') :
    #                     mainDatabase.append(k)
            
    #         #get the list available of bkp database that is running and on firebase bkp database list
    #         splitBkpDatabase = fileInfo['bkpDatabase'].split(",")
            
    #         backup_instance_list = splitting.databaseInstanceList("Backup")
            
    #         bkpDatabase = []
    #         for i in splitBkpDatabase :
    #             for k in backup_instance_list :
    #                 if k.get('Instance_state') == 'running' and i in k.get('Instance_name') :
    #                     bkpDatabase.append(k)
            
    #         file_download = joining.joinAndDecrypt(accountName,fileID,originalName,mainDatabase,bkpDatabase)
    #         return send_file(file_download, as_attachment=True)
        
    #     elif request.form['action'] == "Download Shared File" :
    #         originalName = request.form['fileName']
    #         fileID = request.form['file_id']
    #         accountName = request.form['owner']
            
    #         #get the file info from firebase
    #         fileInfo = fs.getInfoBasedOnId(accountName,fileID)
            
    #         #get the list available database that is running and on firebase database list
    #         splitMainDatabase = fileInfo['mainDatabase'].split(",")
            
    #         instance_list = splitting.allInstanceList("Database")
            
    #         mainDatabase = []
    #         for i in splitMainDatabase :
    #             for k in instance_list:
    #                 if k.get('Instance_state') == 'running' and i in k.get('Instance_name') :
    #                     mainDatabase.append(k)
            
    #         #get the list available of bkp database that is running and on firebase bkp database list
    #         splitBkpDatabase = fileInfo['bkpDatabase'].split(",")
            
    #         backup_instance_list = splitting.databaseInstanceList("Backup")
            
    #         bkpDatabase = []
    #         for i in splitBkpDatabase :
    #             for k in backup_instance_list :
    #                 if k.get('Instance_state') == 'running' and i in k.get('Instance_name') :
    #                     bkpDatabase.append(k)
            
    #         file_download = joining.joinAndDecrypt(accountName,fileID,originalName,mainDatabase,bkpDatabase)
    #         return send_file(file_download, as_attachment=True)
        
    #     elif request.form['action'] == "File description": 
    #         #add it to session before redirect to the page
    #         fileID = request.form['file_id']
    #         session['fileID'] = fileID
    #         return redirect(url_for('fileInfo'))
        
    #     elif request.form['action'] == "Shared File Desc" :
    #         #add it to session before redirect to the page
    #         fileID = request.form['file_id']
    #         owner = request.form['owner']
            
    #         session['fileID'] = fileID
    #         session['owner'] = owner
    #         return redirect(url_for('fileInfo'))

    return redirect(url_for('home'))

# ===================================== File Info / description ============================================================

@app.route('/fileInfo')
def fileInfo() :
    if 'fileID' in session :
        theRecepient = False
        if 'owner' in session :
            accountName = session['owner']
            theRecepient = True
        else : 
            accountName = session['username']
        fileID = session['fileID']
        result = fs.getInfoBasedOnId(accountName,fileID)
        
        dateUpload = result['uploadDate'].replace(tzinfo=timezone.utc).astimezone(tz=None).strftime("%d %b %Y %H:%M:%S")
        
        #popping out the file id, because no needed anymore
        session.pop('fileID', default=None)
        session.pop('owner', default=None)
        
        #get the list of people that got access for this file
        #print(result['shareCode'])
        
        try :
            sharedResult = fs.getCodesInfo(result['shareCode'])
            sharePeople = sharedResult['sharePeople']
        except :
            sharePeople = []

        return render_template('fileInfo.html', result = result, dateUpload = dateUpload, theRecepient= theRecepient, sharePeople = sharePeople)
    
    return redirect(url_for('home'))

#this method consist 2 user stories, create the sharing and revoke the sharing
@app.route('/fileInfo', methods=['GET', 'POST'])
def shareFile() :
    if request.method == 'POST' :
        #if it's share code clicked
        if request.form['action'] == "share code" :
            #adding it to session again, so can route to fileinfo page
            fileID = request.form['fileID']
            session['fileID'] = fileID
            
            accountName = session['username']
            
            result = fs.getInfoBasedOnId(accountName,fileID)
            
            if result['shared'] == False :
                #generate the code
                while(True) :
                    codeGenerated = basic.id_generator()
                    
                    checkIfCodeAvailable = fs.getCodesInfo(codeGenerated)
                    
                    if checkIfCodeAvailable == None :
                        break
                
                #change the value on user database
                fs.updateShareCode(accountName,fileID,codeGenerated)
                
                #add the code to sharedCode database
                fs.addCode(codeGenerated,fileID,accountName)
                
                flash(f'Code Generated! the code is {codeGenerated}', 'success')
            else :
                flash(f'The code already generated, the previous code is {result["shareCode"]}', 'failedCode')
        #if its revoke sharing clicked
        if request.form['action'] == "revoke Sharing" :
            #adding it to session again, so can route to fileinfo page
            fileID = request.form['fileID']
            session['fileID'] = fileID
            
            code = request.form['code']
            
            try :
                #get the list of people that been shared
                codeResult = fs.getCodesInfo(code)
                sharePeople = codeResult['sharePeople']
                
                #get the account name based on list of sharePeople(email)
                accountNameList = []
                
                for i in sharePeople :
                    accountName = fs.getUserNameFromEmail(i)
                    accountNameList.append(accountName)

                #first step delete the code from accountNameList (under account database)
                for accountName in accountNameList :
                    fs.deleteSharedCodeFromAccount(accountName,code)
                    
                #second step delete the code from sharedCode databsae
                fs.deleteCodefromSharedDatabase(code)
            except :
                pass
            
            #third step change the file info from owner's file uploaded
            me = session['username']
            
            fs.revokeShared(me,fileID)
            flash('File sharing revoked', 'success')
             
            
    return redirect(url_for('fileInfo'))

#remove other user from shared list by Email
@app.route('/removeShared', methods =['GET' , 'POST'])
def removeShared() :
    if request.method == 'POST' :
        email = request.form['recipientEmail']
        code = request.form['code']
        
        #this code is for removing the email from sharedList under "sharedCode" collection
        #get the information based on code
        codeResult = fs.getCodesInfo(code)
        sharePeople = codeResult['sharePeople']
        
        #remove it from the array
        sharePeople.remove(email)

        #commit the update to the Firestore
        fs.updateShared(code,codeResult)
        
        #this code is for removing the shared Code that tied to the user under "Account" colection
        #find the user based on the email first
        accountName = fs.getUserNameFromEmail(email)
        
        #remove the code from shared Code (under Account)
        fs.deleteSharedCodeFromAccount(accountName,code)
        
        #to make sure it redirect back to fileInfo
        fileID = request.form['fileID']
        session['fileID'] = fileID
    
    return redirect(url_for('fileInfo'))

#adding new user to share list by Email
@app.route('/addShare', methods =['GET' , 'POST'])
def addShare() :
    if request.method == 'POST' :
        #to make sure it redirect back to fileInfo
        fileID = request.form['fileID']
        session['fileID'] = fileID
        
        code = request.form['code']
        
        email = request.form['email']
        
        #get the current user's email
        me = session['username']
        myInfo = fs.accountInformation(me)
        myEmail = myInfo['email']
        
        #if the user key in their own email throw error
        if myEmail == email :
            flash("You can't add yourself as recipient", 'failedCode2')
            return redirect(url_for('fileInfo'))
            
        #check if user is registered or not
        try :
            accountName = fs.getUserNameFromEmail(email)
        except :
            flash('Recipient not found in our database, please share the code instead', 'failedCode2')
            return redirect(url_for('fileInfo'))

        #this code is adding the userEmail to the sharedList under "sharedCode" collection
        codeResult = fs.getCodesInfo(code)
        sharePeople = codeResult['sharePeople']
        
        if email in sharePeople :
            flash('Recipient already on the list', 'failedCode2')
            return redirect(url_for('fileInfo'))
        
        #add it to the array
        sharePeople.append(email)
        
        #commit the update to the database
        fs.updateShared(code,codeResult)
        
        #this code is for adding the shared Code to the user under "Account" colection
        fs.addtoSharedFile(accountName,code)
    
    return redirect(url_for('fileInfo'))

#change fileName
@app.route('/editFileName', methods=['GET', 'POST'])    
def editFileName() :
    if request.method == 'POST' :
        #to make sure it redirect back to fileInfo
        fileID = request.form['fileID']
        session['fileID'] = fileID
        
        fileName = request.form['fileName']
        accountName = session['username']
        
        fs.updateFileName(accountName,fileID,fileName)

    flash("Successfully edited file name", "success")        
    return redirect(url_for('fileInfo'))

#change password file
@app.route('/editFilePassword', methods=['GET', 'POST'])
def editFilePassword() :
    if request.method == 'POST' :
        
        #to make sure it redirect back to fileInfo
        fileID = request.form['fileID']
        session['fileID'] = fileID
        
        accountName = session['username']
        if request.form['action'] == "change Password" :
            
            password = request.form['password']
            passwordRepeat = request.form['passwordRepeat']
            
            if password != passwordRepeat :
                flash('Password is not same', 'failedCode2')
                return(redirect(url_for('fileInfo')))
            
            #Download the File
            
            originalName = request.form['originalName']
            
            #get the file info from firebase
            fileInfo = fs.getInfoBasedOnId(accountName,fileID)
            
            #get the list available database that is running and on firebase database list
            splitMainDatabase = fileInfo['mainDatabase'].split(",")
            
            instance_list = splitting.allInstanceList("Database")
            
            mainDatabase = []
            for i in splitMainDatabase :
                for k in instance_list:
                    if k.get('Instance_state') == 'running' and i in k.get('Instance_name') :
                        mainDatabase.append(k)
            
            #get the list available of bkp database that is running and on firebase bkp database list
            splitBkpDatabase = fileInfo['bkpDatabase'].split(",")
            
            backup_instance_list = splitting.databaseInstanceList("Backup")
            
            bkpDatabase = []
            for i in splitBkpDatabase :
                for k in backup_instance_list :
                    if k.get('Instance_state') == 'running' and i in k.get('Instance_name') :
                        bkpDatabase.append(k)
            
            file_download = joining.joinAndDecrypt(accountName,fileID,originalName,mainDatabase,bkpDatabase)
            
            #zipping the file
            zipFile = zippingFile.zipFile(file_download,password)
            
            #encrypthing the file
            
            splitting.encryptWithZipfile(zipFile,accountName,fileID,mainDatabase,bkpDatabase)
            
            
            fs.addFilePassword(accountName,fileID)
            
        elif request.form['action'] == "remove Password" :
            password = request.form['password']

            originalName = request.form['originalName']
            
            #get the file info from firebase
            fileInfo = fs.getInfoBasedOnId(accountName,fileID)
            
            #get the list available database that is running and on firebase database list
            splitMainDatabase = fileInfo['mainDatabase'].split(",")
            
            instance_list = splitting.allInstanceList("Database")
            
            mainDatabase = []
            for i in splitMainDatabase :
                for k in instance_list:
                    if k.get('Instance_state') == 'running' and i in k.get('Instance_name') :
                        mainDatabase.append(k)
            
            #get the list available of bkp database that is running and on firebase bkp database list
            splitBkpDatabase = fileInfo['bkpDatabase'].split(",")
            
            backup_instance_list = splitting.databaseInstanceList("Backup")
            
            bkpDatabase = []
            for i in splitBkpDatabase :
                for k in backup_instance_list :
                    if k.get('Instance_state') == 'running' and i in k.get('Instance_name') :
                        bkpDatabase.append(k)
            
            #get the file
            file_download = joining.joinWithPassword(accountName,fileID,originalName,mainDatabase,bkpDatabase)
            
            #unzip it with password
            try :
                zippingFile.unZipFile(file_download,password)
            except :
                flash("wrong password", "failedCode2")
                return redirect(url_for('fileInfo'))
            
            splitting.encrypt(originalName,accountName,fileID)
                
            fs.removeFilePassword(accountName,fileID)
        
    return redirect(url_for('fileInfo'))

if __name__ == '__main__':
    app.run(host="0.0.0.0")