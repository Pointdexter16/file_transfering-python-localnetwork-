import os
from zipfile import ZipFile
import shutil

def zip_dir(path):  
    initial_dir=os.getcwd()
    zipFileName=f'{os.path.basename(path)}.zip'
    with ZipFile(zipFileName,'w') as zipObject: 
        os.chdir(path)
        os.chdir('..')
        for folderName,_,fileName in os.walk(os.path.basename(path)):
            for file in fileName:
                filePath=os.path.join(folderName,file)
                zipObject.write(filePath)
        os.chdir(initial_dir)

    return zipFileName

def unzip_dir(path):
    with ZipFile(path,'r') as zipObject:
        zipObject.extractall()
        
filename=zip_dir("../../photos")
unzip_dir(filename)
os.remove(filename)