#modules imported

import pickle
import socket
import os
import shutil
from termcolor import colored
from pyfiglet import Figlet
from colorama import init,Fore
import readline
import tqdm
import time
import sys
import argparse
from zipfile import ZipFile





#functions

def dir_size(path):
    size=0
    for folderName,_,fileName in os.walk(path):
        for file in fileName:
            filePath=os.path.join(folderName,file)
            size+=os.path.getsize(filePath)
    return size

def byte_gb(size):
    return size/(1024**3)


def complete(text, state):
    for dir in DIRECTOREIES:
        if dir.startswith(text):
            if not state:
                return dir
            else:
                state -= 1


def receive_response():
    resp_len=(conn.recv(HEADER)).decode(FORMAT)
    while resp_len:
        resp_len=int(resp_len)
        response=conn.recv(resp_len).decode(FORMAT)
        return response

def receive_response_list():
    resp_list_len=(conn.recv(HEADER)).decode(FORMAT)
    while resp_list_len:
        resp_list_len=int(resp_list_len)
        response_list_pickle=conn.recv(resp_list_len)
        response_list=pickle.loads(response_list_pickle)
        return response_list

def receive_response_dir():
    data_recv=0
    response_list_pickle=b''
    resp_list_len=(conn.recv(HEADER)).decode(FORMAT)
    resp_list_len=int(resp_list_len)
    if resp_list_len>4096: time.sleep(1) #IT GIVES TIME TO THE CLIENT TO POPULATE THE PIPE WITH DATA COZ WITHOUT IT DATA WAS GETTING LOST 
    while True:                     #HAVE TO FIND A BETTER WAY COZ RESPONSE TIME WILL DEPEND ON THE INTERNET CONNECTION STILL I AM NOT SURE ITS A HUNCH
        if data_recv>=resp_list_len:
            break
        response_list_pickle+=conn.recv(BUFFER_SIZE)
        data_recv+=BUFFER_SIZE
    response_list=pickle.loads(response_list_pickle)
    return response_list

def send_command(command):
    command_encoded=command.encode(FORMAT)
    command_len=len(command_encoded)
    send_length=str(command_len).encode(FORMAT)
    send_length+=b' '*(HEADER-len(send_length))
    conn.send(send_length)
    conn.send(command_encoded)

def send_response_list(response):
    response_pickle=pickle.dumps(response)
    response_pickle_len=len(response_pickle)
    send_length=str(response_pickle_len).encode(FORMAT)
    send_length+=b' '*(HEADER-len(send_length))
    conn.send(send_length)
    conn.send(response_pickle)


def receive_command():
    comm_len=(conn.recv(HEADER)).decode(FORMAT)
    comm_len=int(comm_len)
    command=(conn.recv(comm_len)).decode(FORMAT)
    return command


def send_file(file_path):
    filesize=os.path.getsize(file_path)
    response_encoded=f'{os.path.basename(file_path)}{SEPARATOR}{filesize}'.encode(FORMAT)
    response_len=len(response_encoded)
    send_length=str(response_len).encode(FORMAT)
    send_length+=b' '*(HEADER-len(send_length))
    conn.send(send_length)
    conn.send(response_encoded)
    with open(file_path,'rb') as f:
        while True:
            bytes_read=f.read(BUFFER_SIZE)
            if not bytes_read:
                break
            conn.sendall(bytes_read)
    conn.recv(4)

def send_dir(dir_path):
    dir_file_dic={}
    for dirpath,_,filenames in os.walk(os.path.basename(dir_path)):
        dir_file_dic.update({dirpath:filenames})
    send_response_list(dir_file_dic)
    protocol_completion=receive_command()
    if protocol_completion=='protocol completed successfully':
        for dir,filenames in dir_file_dic.items():
            if bool(filenames):
                for filename in filenames:
                    path_file=os.path.join(dir,filename)
                    send_file(path_file)
    else:
        pass


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
        

def receive_file(main_path='extraction'):
    bytes_received=0
    comm_len=(conn.recv(HEADER)).decode(FORMAT)
    comm_len=int(comm_len)
    command=(conn.recv(comm_len)).decode(FORMAT)
    file_name,filesize=command.split(SEPARATOR)
    filesize=int(filesize)
    progress = tqdm.tqdm(range(filesize), f"Receiving {file_name}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(f'{main_path}/{file_name}', "wb") as f:
        while True:
            if bytes_received==filesize:    
                break
            bytes_read = conn.recv(BUFFER_SIZE)
            bytes_received+=len(bytes_read)
            f.write(bytes_read)
            progress.update(len(bytes_read))
    conn.send('done'.encode('utf-8'))

def receive_dir():
    Zip=int(receive_response())
    if Zip:
        print(Zip)
        file_name=receive_response()
        receive_file()
        os.chdir('extraction')
        unzip_dir(file_name)
        os.remove(file_name)
    else:
        initial_time=time.time()
        dir_dic=receive_response_dir()
        os.chdir('extraction')
        if os.path.exists(list(dir_dic.keys())[0]):
            if input('Enter (y) if you want to overwrite the folder \n')=='y':
                shutil.rmtree(list(dir_dic.keys())[0])
                send_command('protocol completed successfully')       
                for dir in dir_dic:
                    if OS_sys=='Windows':
                        os.mkdir('/'.join(dir.split('\\')))
                    else:
                        os.mkdir(dir)
                for dir,filenames in dir_dic.items():
                    if bool(filenames):
                        for filename in filenames:
                            receive_file(main_path='/'.join(dir.split('\\')))
                            
            else:
                send_command('aboard')
                print('File already exists please try again!')
        else:
            send_command('protocol completed successfully')       
            for dir in dir_dic:
                    if OS_sys=='Windows':
                        os.mkdir('/'.join(dir.split('\\')))
                    else:
                        os.mkdir(dir)
            for dir,filenames in dir_dic.items():
                if bool(filenames):
                    for filename in filenames:
                        receive_file(main_path='/'.join(dir.split('\\')))
        print(time.time()-initial_time)
def client_mode(Connected):
    DIRECTOREIES=[]
    def complete(text, state):
        for dir in DIRECTOREIES:
            if dir.startswith(text):
                if not state:
                    return dir
                else:
                    state -= 1
    print(colored('[YOU HAVE ENTERED CLIENT NAVIGATION MODE....]','white'))
    readline.parse_and_bind("tab: complete")
    readline.set_completer(complete)
    init()
    while Connected:
        try:
            os.chdir('/Users/shehzailabbas/Documents/sheets/socketttt')
            DIRECTOREIES=receive_response_list()
            current_dir=receive_response()
            command=input(colored(current_dir,'white',attrs=['bold'])+Fore.BLUE)
            command=command.strip()
            if command=='switch': send_command('switch');self_mode(Connected)
            elif command=='help':
                send_command(command)
                print('---------------------------------------------------------------')
                print('cd: change directory')
                print('rm: remove directory or file')
                print('get: download directory or file from host computer')
                print('ls: list directories and files')
                print('switch: switch between modes')
                print('com: communicate with the host machine user\n')
                print('NOTE --> if any other command is passed it will simply run it on the host system as a python command and will return the response')
                print('---------------------------------------------------------------')
            elif command=='ls':
                send_command('ls')
                for i in DIRECTOREIES:
                    print(i)
            elif command=='exit()' or command=='quit()':
                send_command(command)
                print('disconnected')
                sys.exit()
            elif command.split(" ")[0]=='get':
                try:
                    os.mkdir("extraction")
                except:
                    pass
                send_command(command)
                is_file=receive_response()
                if is_file=='True':
                    receive_file()
                elif is_file=='False':
                    receive_dir()
                else:
                    print('\n',is_file)
            elif command.split(" ")[0]=='rm':
                send_command(command)
                is_file=receive_response()
            elif command.split(" ")[0]=='cd':
                send_command(command)
            elif command=='com':
                if OS_sys!='Darwin' and OS_sys!='Windows':
                    print("doesn't support!!!")
                else:
                    send_command(command)
                    mess=input("Press enter to start and if you wish to quit this mode enter Q! anytime\n")
                    while(mess!='Q' and mess!='q'):
                        mess=input("message->")
                        send_command(mess)
                        print('sent')
            else:  
                send_command(command)
                resp=receive_response()
                if resp=='c':
                    print(receive_response())
                elif resp=='invalid command':
                    print(resp)
                else:
                    print(receive_response())
                    print(receive_response())
        except Exception as e:
            print('error:',e)

def self_mode(Connected):
    DIRECTOREIES=[]
    def complete(text, state):
        for dir in DIRECTOREIES:
            if dir.startswith(text):
                if not state:
                    return dir
                else:
                    state -= 1
    print(colored('[YOU HAVE ENTERED NAVIGATION MODE....]','white'))
    readline.parse_and_bind("tab: complete")
    readline.set_completer(complete)
    init()
    os.chdir('/Users/shehzailabbas/Documents/sheets/socketttt')
    while Connected:
        try:
            DIRECTOREIES=os.listdir()
            command=input(colored(os.getcwd()+'>','white',attrs=['bold'])+Fore.BLUE)
            command_list=[]
            command=command.strip()
            command_list=command.split(' ',1)
            for i in range(len(command_list)):
                command_list[i]=command_list[i].strip()
            if command=='switch': send_command('switch');client_mode(Connected)
            elif command=='help':
                print('---------------------------------------------------------------')
                print('cd: change directory')
                print('rm: remove directory or file')
                print('send: send directory or file to the host computer')
                print('ls: list directories and files')
                print('switch: switch between modes\n')
                print('NOTE --> if any other command is passed it will simply run it on the host system as a python command and will return the response')
                print('---------------------------------------------------------------')
            elif 'ls' in command:
                for i in DIRECTOREIES:
                    print(i)
            elif command=='exit()' or command=='quit()':
                send_command(command)
                print('disconnected')
                sys.exit()
            elif command_list[0]=='cd':
                if command_list[1]=='..':
                    dir=os.getcwd().split('/')
                    dir.pop(len(dir)-1)
                    path=os.path.join(*dir)
                    os.chdir('/'+path)
                else:
                    path=os.path.join(os.getcwd(),command_list[1])
                    try:
                        if path==os.getcwd():
                            os.chdir(command_list[1])
                        else:
                            os.chdir(path)
                    except Exception as e:
                        print(e)
            elif command_list[0]=='send':
                send_command('send')
                true_path=command_list[1]
                if os.path.isfile(true_path):
                    send_command('file')
                    send_file(true_path)
                elif os.path.isdir(true_path):
                    send_command('dir')
                    send_dir(true_path)
                else:
                    send_command('nothing')
                    print("directory or the file specified doesn't exist")
            elif command_list[0]=='rm':
                path=os.path.join(os.getcwd(),command_list[1])
                try:
                    if not os.path.exists(path):
                        print("directory or the file specified doesn't exist")
                    else:
                        if os.path.isdir(path):
                            shutil.rmtree(path)
                        elif os.path.isfile(path):
                            os.remove(path)
                except:
                    print('OOPS!something went wrong')
            else:
                exec(command)
        except Exception as e:
            print('error')
            print(e)

#initialization
DIRECTOREIES=[]

parser=argparse.ArgumentParser()
parser.add_argument('-i','--ipAddress',help='pass ip address you want to use for the connection')
parser.add_argument('-p','--port',help='pass port you want to use for the connection')
args=parser.parse_args()

dirpath='/Users/shehzailabbas/Documents/sheets/socketttt/extraction/files'
filespath='/Users/shehzailabbas/Documents/sheets/socketttt/extraction'

SERVER=args.ipAddress if args.ipAddress else '192.168.29.74'
PORT=int(args.port) if args.port else 5050


FORMAT='utf-8'
ADDR=(SERVER,PORT)
HEADER=64
SEPARATOR='<SEPARATOR>'
BUFFER_SIZE=4096

socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
socket.bind(ADDR)


#server listening
socket.listen()
print(f'[SERVER LISTENING AT {SERVER}]......')
conn,addr=socket.accept()
print(f'[SERVER CONNECTED TO {addr}]')
Connected=True
#main code
a=input(['PRESS 1 TO ACCESS DIRECTORYIES OF CLIENT AND PRESS 2 TO ACCESS YOUR DIRECTORYIES'])
f = Figlet(font='banner3-D',) 
print(colored(f.renderText('REACKT'),'red'))
send_command(a)
OS_sys=receive_command()
print("OS:",OS_sys)
if a=='1':
    client_mode(Connected)

elif a=='2':
    self_mode(Connected)

        

