from binascii import hexlify, unhexlify
import subprocess
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.SecretSharing import Shamir

import os
import boto3
import paramiko

import shutil
import re

AWS_REGION = "ap-northeast-1"
EC2_RESOURCE = boto3.resource('ec2', region_name=AWS_REGION)

Ec2key_name = "write your key here"
#example 
#Ec2key_name = "ANGELVOC.PEM"

#sending a command to the instance, and get the reply back
def sendCommand(command, instance_list, backup_instance_list) :
    arrayTest = []
    
    for i in instance_list :
        if i["Instance_state"] == "running" :
            dnsServer = i['Instance_dns']
    
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            dnsServer,
            username= 'ubuntu',
            key_filename=Ec2key_name
        )
        stdin, stdout, stderr = ssh.exec_command(command)
        stdin.flush()
        data = stdout.read().splitlines()
        for line in data:
            arrayTest.append(line.decode())
        ssh.close()
    
    for i in backup_instance_list :
        if i["Instance_state"] == "running" :
            dnsServer = i['Instance_dns']
    
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            dnsServer,
            username= 'ubuntu',
            key_filename=Ec2key_name
        )
        stdin, stdout, stderr = ssh.exec_command(command)
        stdin.flush()
        data = stdout.read().splitlines()
        for line in data:
            arrayTest.append(line.decode())
        ssh.close()
        

#deleting all the saved data from the instance that online
def deleteAngelVOC(instance_list, backup_instance_list, accountName) :
    sendCommand(f"rm -r {accountName}", instance_list, backup_instance_list)

def startInstance(instance_ID) :
    
    instance = EC2_RESOURCE.Instance(instance_ID)
    instance.start()
            
    print(f'Starting EC2 instance: {instance.id}')

#    instance.wait_until_running()

    print(f'EC2 instance "{instance.id}" has been started')
            
def stopInstance(instance_ID) :

    instance = EC2_RESOURCE.Instance(instance_ID)
    instance.stop()
    
    print(f'Stopping EC2 instance: {instance.id}')

#    instance.wait_until_stopped()

    print(f'EC2 instance "{instance.id}" has been stopped')
    
#forcing all instance to be running
def startAllInstance(databaseInstance, backupInstance) :
    
    for enum,i in enumerate(databaseInstance) :
        if i["Instance_state"] == "stopped" and enum != (len(databaseInstance) -1):
            instance = EC2_RESOURCE.Instance(i['Instance_ID'])
            instance.start()
            
            print(f'Starting EC2 instance: {instance.id}')
            
        elif i["Instance_state"] == "stopped" and enum == (len(backupInstance) -1) :
            instance = EC2_RESOURCE.Instance(i['Instance_ID'])
            instance.start()
            
            print(f'Starting EC2 instance: {instance.id}')
    
            instance.wait_until_running()

            print(f'All the main database instance has been started')
    
    for enum,i in enumerate(backupInstance) :
        if i["Instance_state"] == "stopped" and enum != (len(backupInstance) -1):
            instance = EC2_RESOURCE.Instance(i['Instance_ID'])
            instance.start()
            
            print(f'Starting EC2 instance: {instance.id}')
            
        elif i["Instance_state"] == "stopped" and enum == (len(backupInstance) -1) :
            instance = EC2_RESOURCE.Instance(i['Instance_ID'])
            instance.start()
            
            print(f'Starting EC2 instance: {instance.id}')
    
            instance.wait_until_running()

            print(f'All the backup database instance has been started')

#Get Instance that running
def databaseInstanceList(whatToFind) :
        instance_list = [{}]

        instances = EC2_RESOURCE.instances.all()

        for instance in instances:
            for tag in instance.tags :
                if tag['Key'] == 'Name' and whatToFind in tag['Value'] and instance.state["Name"] == 'running' :
                    newList = {
                        "Instance_ID" : instance.id,
                        "Instance_name" : tag['Value'],
                        "Instance_state" : instance.state["Name"],
                        "Instance_dns" : instance.public_dns_name
                    }
                    instance_list.append(newList)
        
        del instance_list[0]
        return instance_list
    
def allInstanceList(whatToFind) :
        instance_list = [{}]

        instances = EC2_RESOURCE.instances.all()

        for instance in instances:
            for tag in instance.tags :
                if tag['Key'] == 'Name' and whatToFind in tag['Value'] :
                    newList = {
                        "Instance_ID" : instance.id,
                        "Instance_name" : tag['Value'],
                        "Instance_state" : instance.state["Name"],
                        "Instance_dns" : instance.public_dns_name
                    }
                    instance_list.append(newList)
        
        del instance_list[0]
        return instance_list


def auto_directory(folderName) :
    isExist = os.path.exists(folderName)
    if not isExist :
        os.makedirs(folderName)
        return (folderName)       
    else :
        return (folderName)
    
def splitFile(fileName,directories) :
        
    with open(fileName, 'rb') as file:
        splitting(file,fileName,directories)

def splitting(file,fileName, directories) :
    read_buffer_size = 1024
    current_chunk_size = 0
    current_chunk = 1
    done_reading = False
    
    #read the file size 
    file_size = os.stat(fileName).st_size
    
    total_directory = len(directories)
    
    # plus 1000 means , we gonna put 1 kb extra for the early file, except the last file 
    chunk_size = int(file_size / total_directory) + 1024
    
    #this will loop until the chunk_size that allowed and then create a new chunk file for it
    
    while not done_reading :
        for i in directories :
            with open(f'{i}/{current_chunk}.chk', 'ab') as chunk:
                while True:
                    #reading file per buffer size
                    bfr = file.read(read_buffer_size)
                    #if the reading not contain any bytes or null
                    if not bfr:
                        done_reading = True
                        break
                            
                    #writing the buffer into the chunk file
                    chunk.write(bfr)
                            
                    #updating chunk size everytime it writen to the the file
                    current_chunk_size += len(bfr)
                            
                    #checking if its exceeding chunk size from the top, if yes it will break from the while loop and go for new file
                    if current_chunk_size + read_buffer_size > chunk_size:
                        current_chunk += 1
                        current_chunk_size = 0
                        break
                    
def sendFile(instance_list, backup_instance_list,accountName) :
    
    '''
    for enum,i in enumerate(instance_list) :
        if i['Instance_state'] == "running" :
            dnsAddress = i ['Instance_dns']
            subprocess.check_output(f'scp -i "{Ec2key_name}" -q -r ubuntu@{dnsAddress}:/home/ubuntu/{AccountName}/2 "{AccountName}/instance{enum+1}/",shell= True')
    '''
    for enum,i in enumerate(instance_list) :
        if i['Instance_state'] == "running" :
            dnsAddress = i['Instance_dns']
            checker = getDirectoryInfo(dnsAddress,"ls")
            if accountName in checker :
                subprocess.run(f'scp -i "{Ec2key_name}" -q -r "{accountName}/instance{enum+1}/"* ubuntu@{dnsAddress}:/home/ubuntu/{accountName}',shell= True)
                print(f'File sent to database server {i["Instance_name"]}')
            else :
                subprocess.run(f'scp -i "{Ec2key_name}" -q -r "{accountName}/instance{enum+1}/" ubuntu@{dnsAddress}:/home/ubuntu/{accountName}',shell= True)
                print(f'File sent to database server {i["Instance_name"]}')
    
    for enum,i in enumerate(backup_instance_list) :
        if i['Instance_state'] == "running" :
            dnsAddress = i['Instance_dns']
            checker = getDirectoryInfo(dnsAddress,"ls")
            if accountName in checker :
                subprocess.run(f'scp -i "{Ec2key_name}"-q -r "{accountName}/instance{enum+1}/"* ubuntu@{dnsAddress}:/home/ubuntu/{accountName}',shell= True)
                print(f'File sent to database server {i["Instance_name"]}')
            else :
                subprocess.run(f'scp -i "{Ec2key_name}" -q -r "{accountName}/instance{enum+1}/" ubuntu@{dnsAddress}:/home/ubuntu/{accountName}',shell= True)
                print(f'File sent to database server {i["Instance_name"]}')
            
def encrypt(fileName,accountName,u_id) :
    
    #generate random key
    key = get_random_bytes(16)
    
    #file that we want to encrypt, should be passed from app.py later)
    #fileName = "testing.mp4"
    
    #get the file name and remove the extensions
    outputFile = os.path.splitext(fileName)[0]
    
    #getting the list of database available
    instance_list = databaseInstanceList("Database")
    
    #getting the list of database backup
    backup_instance_list = databaseInstanceList("Backup") 
    
    #Encrypting and splitting file logic start here
    #encrypting with Shamir secret sharing
    #total share of key and threshold
    #logic to get the lowest instance that is currently online (from main database and backup)
    sharex = len(instance_list)
    #if the backup number is lower then main database that online, swap it
    if (len(backup_instance_list) < len(instance_list)) :
        sharex = len(backup_instance_list)
    
    #logic for the threshold of the key needed
    #this logic taking action if the threshold is less then 2, will just do sharex - 1 (it only happen when sharex is 3)
    threshold = int(sharex / 2)
    if (threshold < 2) :
        threshold = sharex - 1
        
    #pruning the instance, so it match of the sharex

    while (len(instance_list) != sharex) :
        instance_list.pop()
    
    
    while (len(backup_instance_list) != sharex) :
        backup_instance_list.pop()
    
    #calling shamir library to generate
    shares = Shamir.split(threshold, sharex, key)

    #adding file extenstion to encrypted file
    outputFile = outputFile + ".encrypted"
    
    #make a new file and encrypting the old file
    with open(fileName, "rb") as fi, open(outputFile, "wb") as fo:
        cipher = AES.new(key, AES.MODE_EAX)
        
        nonce = cipher.nonce
        ct, tag = cipher.encrypt(fi.read()), cipher.digest()
        fo.write(nonce + tag + ct)
    
    #make a folder and save the key inside of it    
    directories = []
    
    for i in range(sharex) :
        newDirectory = auto_directory(f"{accountName}/instance{i+1}/{u_id}")
        directories.append(newDirectory)
    
    #Creating shares file(s)         
    for idx, share in shares:
        x = directories[idx-1]
        url = f'{x}/{idx}.keyshare'
           
        with open(url,"w") as fw :
            fw.write(f'{idx}-{hexlify(share).decode()}')
    
    #Splitting the file into small chunk        
    splitFile(outputFile,directories)
    
    #This is the start of sending file function
    
    
    #sending file
    sendFile(instance_list,backup_instance_list,accountName)
    
    #remove everything after its done
    
    #remove the original file

    if os.path.isfile(fileName) :
        os.remove(fileName)
    
    #remove the encrypted file
    if os.path.isfile(outputFile) :
        os.remove(outputFile)
    
    #remove the folder that stored the data
    deleteFolder = accountName + "/"
    if os.path.isdir(f'{deleteFolder}') :
        shutil.rmtree(deleteFolder, ignore_errors=True)
    
    

def encryptWithZipfile(fileName,accountName,u_id,instance_list,backup_instance_list) :
        #generate random key
    key = get_random_bytes(16)
    
    #file that we want to encrypt, should be passed from app.py later)
    #fileName = "testing.mp4"
    
    #get the file name and remove the extensions
    outputFile = os.path.splitext(fileName)[0]
    
    #Encrypting and splitting file logic start here
    #encrypting with Shamir secret sharing
    #total share of key and threshold
    #logic to get the lowest instance that is currently online (from main database and backup)
    sharex = len(instance_list)
    
    #logic for the threshold of the key needed
    #this logic taking action if the threshold is less then 2, will just do sharex - 1 (it only happen when sharex is 3)
    threshold = int(sharex / 2)
    if (threshold < 2) :
        threshold = sharex - 1
        
    #pruning the instance, so it match of the sharex

    while (len(instance_list) != sharex) :
        instance_list.pop()
    
    
    while (len(backup_instance_list) != sharex) :
        backup_instance_list.pop()
    
    #calling shamir library to generate
    shares = Shamir.split(threshold, sharex, key)

    #adding file extenstion to encrypted file
    outputFile = outputFile + ".encrypted"
    
    #make a new file and encrypting the old file
    with open(fileName, "rb") as fi, open(outputFile, "wb") as fo:
        cipher = AES.new(key, AES.MODE_EAX)
        
        nonce = cipher.nonce
        ct, tag = cipher.encrypt(fi.read()), cipher.digest()
        fo.write(nonce + tag + ct)
    
    #make a folder and save the key inside of it    
    directories = []
    
    for i in range(sharex) :
        newDirectory = auto_directory(f"{accountName}/instance{i+1}/{u_id}")
        directories.append(newDirectory)
    
    #Creating shares file(s)         
    for idx, share in shares:
        x = directories[idx-1]
        url = f'{x}/{idx}.keyshare'
           
        with open(url,"w") as fw :
            fw.write(f'{idx}-{hexlify(share).decode()}')
    
    #Splitting the file into small chunk        
    splitFile(outputFile,directories)
    
    #This is the start of sending file function
    
    
    #sending file
    sendFile(instance_list,backup_instance_list,accountName)
    
    #remove everything after its done
    
    #remove the original file
    
    
    if os.path.isfile(fileName) :
        os.remove(fileName)
    
    #remove the encrypted file
    if os.path.isfile(outputFile) :
        os.remove(outputFile)
    
    #remove the folder that stored the data
    deleteFolder = accountName + "/"
    if os.path.isdir(f'{deleteFolder}') :
        shutil.rmtree(deleteFolder, ignore_errors=True)
    
    
def getDirectoryInfo(dnsServer,command) :
    arrayTest = []
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        dnsServer,
        username= 'ubuntu',
        key_filename=Ec2key_name
    )
    stdin, stdout, stderr = ssh.exec_command(command)
    stdin.flush()
    data = stdout.read().splitlines()
    for line in data:
        arrayTest.append(line.decode())
    ssh.close()
    return arrayTest

def getVolume(instance_list) :
    arrayTest = []
    command = 'df -hT /dev/root'

    for i in instance_list :
        if i["Instance_state"] == "running" :
            dnsServer = i['Instance_dns']
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                dnsServer,
                username= 'ubuntu',
                key_filename=Ec2key_name
            )
            stdin, stdout, stderr = ssh.exec_command(command)
            stdin.flush()
            data = stdout.read().splitlines()
            for line in data:
                arrayTest.append(line.decode())
            ssh.close()
        
            wordList = []
            for i in arrayTest :
                wordList.append(re.findall("[0-9].[0-9]G", i))
            
            volume = []
            remove_empty = [ele for ele in wordList if ele != []]    
            for i in remove_empty :
                for j,k in enumerate(i) :
                    if j == 1 :
                        volume.append(k.split("G")[0])    
    return volume

def main() :
#    encrypt("notepad.txt")

    #to delete the file
    #getting the list of database available
    instance_list = databaseInstanceList("Database")
    
    #getting the list of database backup
    backup_instance_list = databaseInstanceList("Backup")
    
    instance_volume = getVolume(instance_list)
    
    backup_volume = getVolume(backup_instance_list)
    
    print("main Instance")
    print(instance_volume)
    print("----------------------------------")
    print("backup instance")
    print(backup_volume)
    '''
    accountName = "testing" 
    deleteAngelVOC(instance_list,backup_instance_list, accountName)
    '''
    
    '''
    test = getDirectoryInfo("ec2-54-199-19-213.ap-northeast-1.compute.amazonaws.com", "ls")
    if "testing" in test :
        print("found it ")
    '''
        
if __name__ == '__main__' :
    main()
