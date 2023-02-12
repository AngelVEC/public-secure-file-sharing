import firebase_admin
from firebase_admin import credentials, firestore, auth

#setup
cred = credentials.Certificate("customFirebase/serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

#change the authentication email
def changeEmail(oldEmail,newEmail) :
    user = auth.get_user_by_email(oldEmail)
    auth.update_user(user.uid, email = newEmail)
    
#change the database inside email
def changeDatabaseEmail(accountName, newEmail) :
    db.collection('account').document(accountName).update({"email" : newEmail})

#find document with known accountName / key
def accountInformation(accountName) :
    result = db.collection('account').document(accountName).get()
    
    return result.to_dict()

#get all document in the collection of account
def getAllDocument() :
    result = db.collection('account').get()
    
    allresult = []
    for results in result :
        allresult.append(results.to_dict())
    return allresult

#get all file info
def getallFileinfo(accountName) :
    result = db.collection('account').document(accountName).collection("file").get()
    
    allResult = []
    for results in result :
        allResult.append(results.to_dict())
    return allResult

#get file info based on the ID
def getInfoBasedOnId (accountName,id) :
    result = db.collection('account').document(accountName).collection("file").document(id).get().to_dict()
    
    return result

#get info based on file name
def getInfoBasedOnFileName (accountName,fileName) :
    result = db.collection('account').document(accountName).collection("file").where("fileName", "==", fileName).get()
    
    queryResult = []
    for results in result :
        queryResult.append(results.to_dict())
    
    return queryResult

#update fileName
def updateFileName(accountName,fileID,newfileName) :
    db.collection('account').document(accountName).collection("file").document(fileID).update({"fileName" : newfileName})
    
#update share and code
def updateShareCode(accountName,fileID,code) :
    db.collection('account').document(accountName).collection("file").document(fileID).update(
        {
            "shared" : True,
            "shareCode" : code
        }
    )

def doesEmailExist(email):
    result = db.collection('account').where("email", "==", email).get()
    queryResult = {}
    for results in result :
        queryResult = results.to_dict()
    return len(queryResult) > 0

def getUserNameFromEmail (email) :
    result = db.collection('account').where("email", "==", email).get()
    
    for results in result :
        queryResult = results.to_dict()
    
    userName = queryResult['userName']
    return userName
    
#update fileCount
def updatefileCount(accountName, fileCount) :
    db.collection('account').document(accountName).update({"fileAdded" : fileCount})
    
#add new account to the firestore
def addNewAccount(email,accountName) :
    data = {
        "email" : email,
        "userName" : accountName,
        "role" : "user",
        "fileAdded" : 0
    }
    db.collection('account').document(accountName).set(data)

#get the highest id that can be found in the database
def findHighestcurrentID (accountName) :
    result = getallFileinfo(accountName)
    highestID = 0
    for i in result :
        if i['id'] > highestID :
            highestID = i['id']
    
    return highestID
    
#add new file to the known user
def addNewFileToUser(accountName,fileName,InstanceNumber,bkpInstanceNumber,fileSize) :
    accountInfo = accountInformation(accountName)
    totalCurrentFile = accountInfo['fileAdded']
    
    idForThisFile = totalCurrentFile + 1
    
    #if there is atleast 1 database found stored on it
    if totalCurrentFile > 0 :
        data = {
        "fileName" : fileName,
        "id" : idForThisFile,
        "mainDatabase" : InstanceNumber,
        "bkpDatabase" : bkpInstanceNumber,
        "uploadDate" : firestore.SERVER_TIMESTAMP,
        "shared" : False,
        "fileSize" : fileSize,
        "havePassword" : False
        } 

        db.collection('account').document(accountName).collection("file").document(str(idForThisFile)).set(data)
        
    #this means that user never upload file yet
    else :
        data = {
        "fileName" : fileName,
        "id" : 1,
        "mainDatabase" : InstanceNumber,
        "bkpDatabase" : bkpInstanceNumber,
        "uploadDate" : firestore.SERVER_TIMESTAMP,
        "shared" : False,
        "fileSize" : fileSize,
        "havePassword" : False
        } 

        db.collection('account').document(accountName).collection("file").document(str(idForThisFile)).set(data)
        
    #and update the fileAdded
    updatefileCount(accountName,idForThisFile)
    
    
#delete the file from database
def deleteFileFromDatabase(accountName,fileID) :
    db.collection('account').document(accountName).collection("file").document(fileID).delete()

def userNameCheckIfExist(userName) :
    result = db.collection('account').limit(1).where("userName", "==", userName).get()
    query = None
    
    for i in result :
        query = i.to_dict()
    
    if query :
        return True
    else :
        return False
    
#get all document in the collection of account
def getCodesInfo(code) :
    result = db.collection('sharedCode').document(code).get()
    
    return result.to_dict()

#add to sharedCode database
def addCode(code,fileID,accountName) :
    data = {
        "code" : code,
        "fileID" : fileID,
        "owner" : accountName,
        "sharePeople" : []
    }
    
    db.collection('sharedCode').document(code).set(data)    

#update the sharedPeople
def updateShared(code,data) :
    db.collection('sharedCode').document(code).set(data)

#add to sharedFile (account)
def addtoSharedFile(accountName, code) :
    data = {
        "code" : code
    }
    db.collection('account').document(accountName).collection('sharedFile').document(code).set(data)
    
def deleteSharedCodeFromAccount(accountName,code) :
    db.collection('account').document(accountName).collection('sharedFile').document(code).delete()

def deleteCodefromSharedDatabase(code) :
    db.collection('sharedCode').document(code).delete()

def revokeShared(accountName,id) :
    data = {
        "shared" : False,
        "shareCode" : firestore.DELETE_FIELD
    }
    db.collection('account').document(accountName).collection('file').document(id).update(data)
    
def getAlltheListofSharedFile(accountName) :
    result = db.collection('account').document(accountName).collection('sharedFile').get()
    
    allResult = []
    
    for i in result :
        allResult.append(i.to_dict())
        
    return allResult

def addFilePassword(accountName, id) :
    data = {
        "havePassword" : True
    }
    db.collection('account').document(accountName).collection('file').document(id).update(data)
    
def removeFilePassword(accountName, id) :
    data = {
        "havePassword" : False
    }
    db.collection('account').document(accountName).collection('file').document(id).update(data)

#to test purpose            
def main():
    '''
    #getallListofsharedFile
    accountName = "kalamaritest"
    getAlltheListofSharedFile(accountName)
    '''
    
    '''
    # example of getting email
    accountName = "testing1232456"
    searchuser = accountInformation(accountName)

    print(searchuser)
    '''
    
    '''
    #example getting all collection
    result = getAllDocument()
    print(result)
    '''
    
    
    '''
    #example get file that have been stored by the user
    result = getallFileinfo("testing")
    
    sum = 0
    sumbytes = 0
    sumkilobytes = 0
    summegabytes = 0
    sumgigabytes = 0


    for i in result :
        if 'Bytes' in i['fileSize'] :
            number = int(i['fileSize'].split(' ')[0])
            sumbytes = sumbytes + number

        elif 'kB' in i['fileSize'] :
            number1 = int(i['fileSize'].split(' ')[0])
            sumkilobytes = sumkilobytes + number1 * 1000 

        elif 'MB' in i['fileSize'] :
            number2 = int(i['fileSize'].split(' ')[0])
            summegabytes = summegabytes + number2 * 1000000
        
        elif 'GB' in i['fileSize'] :
            number3 = int(i['fileSize'].split(' ')[0])
            sumgigabytes = sumgigabytes + number3 * 1000000000
        
    sum = sumbytes + sumgigabytes + sumkilobytes + summegabytes
    print(sum)
    '''
    '''
    #get info based on file id
    fileID = "1"
    result = getInfoBasedOnId("testing",fileID)
    print(result)
    '''
    '''
    #example get the information based on file name
    result = getInfoBasedOnFileName("AngelVOC","testing.mp4")
    print(result)
    '''
    
    '''
    #example of updating file name
    updateFileName("AngelVOC","1","testing1234123.mp4")
    '''
    
    '''
    #example storing new account information
    email = "AngelVOC@gmail.com"
    name = "AngelVOC"
    addNewAccount(email,name)
    '''
    
    '''
    #example of user adding new file
    name = "testing1234"
    fileName = "testing.txt"
    addNewFileToUser(name,fileName)
    '''
    
    '''
    #deleting data entry 
    deleteFileFromDatabase("testing1234","3")
    '''
    
    '''
    result = getUserNameFromEmail(str.lower("AngelVOC@gmail.com"))
    print(result)
    '''
    '''
    #check if user is in the firebase
    
    result = userNameCheckIfExist("AngelVOC")
    print(result)
    '''
    
    '''
    accountName = "testing1232456"
    fileID = "1"
    revokeShared(accountName,fileID)
    '''
    
    print(getInfoBasedOnId("kalamaritest","8"))
            
if __name__ == "__main__":
    main()