import pyminizip
import os

def zipFile(fileName, password):
    removePath = os.path.basename(fileName)
    temp = os.path.splitext(removePath)
    
    fileName = str(fileName)
    
    outputName = temp[0] + ".zip"
    
    print(outputName)
    
    com_lvl = 5

    print(fileName,outputName,password,com_lvl)
    pyminizip.compress(fileName, None, outputName, password, com_lvl)
    
    return outputName

def unZipFile(zipFile,password) :

    zipFile = str(zipFile)
    pyminizip.uncompress(zipFile,password, "./", 0)

def unZipFile2(zipFile,password,path) :

    zipFile = str(zipFile)
    pyminizip.uncompress(zipFile,password, path, 0)
    
          
def main():
    #zip the file
    '''
    fileName = "abcda11.txt"
    password = "thisisthepassword"
    zipFile(fileName,password)
    '''
    
    '''
    #unzip the file
    zipFile = "abcda11.zip"
    password = "thisisthepassword"
    
    unZipFile(zipFile,password)
    '''
    test = "download/testing/3/abcda11.txt"
    print(os.path.basename(test))
    print(os.path.dirname(test))

if __name__ == "__main__":
    main()