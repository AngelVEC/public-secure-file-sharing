from binascii import hexlify, unhexlify
import shutil
import subprocess
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.SecretSharing import Shamir

import os
import boto3
import pathlib
import customPy.splitting as splitting

AWS_REGION = "ap-northeast-1"
EC2_RESOURCE = boto3.resource('ec2', region_name=AWS_REGION)

Ec2key_name = "write your key here"
#example 
#Ec2key_name = "ANGELVOC.PEM"

def getFile(instance_list,backup_instance_list,accountName, file_id) :
    
    for i in instance_list :
        if i['Instance_state'] == "running" :
            dnsAddress = i['Instance_dns']
            subprocess.check_output(f'scp -i "{Ec2key_name}" -q -r ubuntu@{dnsAddress}:/home/ubuntu/{accountName}/{file_id}/ "temp/{accountName}/" ',shell= True)
            print(f'File received from database server {i["Instance_name"]}')
    
    for i in backup_instance_list :
        if i['Instance_state'] == "running" :
            dnsAddress = i['Instance_dns']
            subprocess.check_output(f'scp -i "{Ec2key_name}" -q -r ubuntu@{dnsAddress}:/home/ubuntu/{accountName}/{file_id}/ "temp/{accountName}/" ',shell= True)
            print(f'File received from database backup server {i["Instance_name"]}')

def joinAndDecrypt(accountName, file_id, originalFileName,instance_list,backup_instance_list) :
    read_buffer_size = 1024
    
    #creatingVariable
    tempFileDirectory = f"temp/{accountName}/{file_id}"
    encryptedFileName = "temporary.encrypt"
    outputDirectory = f"download/{accountName}/{file_id}"
    
    #create the temp folder
    splitting.auto_directory(tempFileDirectory)
    
    #get the file from server and save it to temp folder
    
    getFile(instance_list,backup_instance_list,accountName,file_id)
    
    #joining file into 1 file
    p = pathlib.Path(tempFileDirectory)
    chunks = list(p.glob('*.chk'))
    #sorting the file
    chunks.sort()
        
    fileLocation = f"{tempFileDirectory}/{encryptedFileName}"
    filePath = pathlib.Path(fileLocation)
    
    #check if the temp file is already exist (have been constructed before) or not
    if filePath.is_file() :
        #remove it first
        os.remove(filePath)
        with open(f'{fileLocation}', 'ab') as file :
                    for chunk in chunks :
                        with open (chunk, 'rb') as piece:
                            while True :
                                bfr = piece.read(read_buffer_size)
                                if not bfr:
                                    break
                                file.write(bfr)
    else :
        with open(f'{fileLocation}', 'ab') as file :
                    for chunk in chunks :
                        with open (chunk, 'rb') as piece:
                            while True :
                                bfr = piece.read(read_buffer_size)
                                if not bfr:
                                    break
                                file.write(bfr)
                            
    #decrypt the file with the keyshare
    
    splitting.auto_directory(outputDirectory)
    
    keyShare = list(p.glob('*.keyshare'))
    shares = []
    
    for i in keyShare :
        
        with open(i,"r") as fr :
            readData = fr.read()
        
        idx, share = [ str.strip(s) for s in readData.split("-") ]
        shares.append((int(idx), unhexlify(share)))
    
    key = Shamir.combine(shares)
    
    #Read the data of encrypted file
    with open(filePath, "rb") as fi:
        nonce, tag = [ fi.read(16) for x in range(2) ]
        cipher = AES.new(key, AES.MODE_EAX, nonce)
        try:
            result = cipher.decrypt(fi.read())
            cipher.verify(tag)
            
            #Constructing the File
            
            outputPath = pathlib.Path(f"{outputDirectory}/{originalFileName}")
            if outputPath.is_file() :
                os.remove(outputPath)
                
                with open(outputPath, "wb") as fo:
                    fo.write(result)
            else :    
                with open(outputPath, "wb") as fo:
                    fo.write(result)
                
        except Exception as e :
            print(e)

    #remove the temp folder
    deleteFolder = f'temp/{accountName}'
    if os.path.isdir(f'{deleteFolder}') :
        shutil.rmtree(deleteFolder, ignore_errors=True)
    
    return outputPath

def joinWithPassword(accountName, file_id, originalFileName,instance_list,backup_instance_list) :
    read_buffer_size = 1024
    
    #creatingVariable
    tempFileDirectory = f"temp/{accountName}/{file_id}"
    encryptedFileName = "temporary.encrypt"
    outputDirectory = f"download/{accountName}/{file_id}"
    
    #create the temp folder
    splitting.auto_directory(tempFileDirectory)
    
    #get the file from server and save it to temp folder
    
    getFile(instance_list,backup_instance_list,accountName,file_id)
    
    #joining file into 1 file
    p = pathlib.Path(tempFileDirectory)
    chunks = list(p.glob('*.chk'))
    #sorting the file
    chunks.sort()
        
    fileLocation = f"{tempFileDirectory}/{encryptedFileName}"
    filePath = pathlib.Path(fileLocation)
    
    #check if the temp file is already exist (have been constructed before) or not
    if filePath.is_file() :
        #remove it first
        os.remove(filePath)
        with open(f'{fileLocation}', 'ab') as file :
                    for chunk in chunks :
                        with open (chunk, 'rb') as piece:
                            while True :
                                bfr = piece.read(read_buffer_size)
                                if not bfr:
                                    break
                                file.write(bfr)
    else :
        with open(f'{fileLocation}', 'ab') as file :
                    for chunk in chunks :
                        with open (chunk, 'rb') as piece:
                            while True :
                                bfr = piece.read(read_buffer_size)
                                if not bfr:
                                    break
                                file.write(bfr)
                            
    #decrypt the file with the keyshare
    
    splitting.auto_directory(outputDirectory)
    
    keyShare = list(p.glob('*.keyshare'))
    shares = []
    
    for i in keyShare :
        
        with open(i,"r") as fr :
            readData = fr.read()
        
        idx, share = [ str.strip(s) for s in readData.split("-") ]
        shares.append((int(idx), unhexlify(share)))
    
    key = Shamir.combine(shares)
    
    originalFileName = os.path.splitext(originalFileName)[0] + ".zip"
    
    #Read the data of encrypted file
    with open(filePath, "rb") as fi:
        nonce, tag = [ fi.read(16) for x in range(2) ]
        cipher = AES.new(key, AES.MODE_EAX, nonce)
        try:
            result = cipher.decrypt(fi.read())
            cipher.verify(tag)
            
            #Constructing the File
            
            outputPath = pathlib.Path(f"{outputDirectory}/{originalFileName}")
            if outputPath.is_file() :
                os.remove(outputPath)
                
                with open(outputPath, "wb") as fo:
                    fo.write(result)
            else :    
                with open(outputPath, "wb") as fo:
                    fo.write(result)
                
        except Exception as e :
            print(e)

    #remove the temp folder
    deleteFolder = f'temp/{accountName}'
    if os.path.isdir(f'{deleteFolder}') :
        shutil.rmtree(deleteFolder, ignore_errors=True)
    
    return outputPath
                
def main() :
    accountName = "kalamaritest"
    file_id = 1    
    originalFileName = "notepad3.txt"
    joinAndDecrypt(accountName,file_id,originalFileName)
    '''
    #getFile
    #getting the list of database available
    instance_list = splitting.databaseInstanceList("Database")
    
    #getting the list of database backup
    backup_instance_list = splitting.databaseInstanceList("Backup")
    accountName = 'kalamaritest'
    file_id = 1
    
    getFile(instance_list,backup_instance_list,accountName,file_id)
    '''
    
if __name__ == '__main__' :
    main()