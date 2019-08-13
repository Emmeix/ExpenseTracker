#!/usr/bin/python3
import socket
import time
import requests
import getpass

def service_check(usr, passw):
    req = requests.session()
    req.post('http://localhost:5000/login', data={'username': usr, 'password': passw})
    def check_service(ip, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ch = sock.connect_ex((ip, port))
        sock.close()
        return ch

    services = [
        ("DNS", '192.168.1.82', 53),
        ("DNS Web", '192.168.1.82', 80),
        ("SMB", '192.168.1.121', 139),
    ]

    while True:
        statfile = open(".statfile.log", "w+")
        for s in services:
            check = check_service(s[1], s[2])
            print("%s is %s" % (s[0], "up" if check == 0 else "down"))
            statfile.write("%s is %s" % (s[0], "up\n" if check == 0 else "down"))
            statfile.write("\n")

            if check == 0:
                stu = s[0] + " is up"
                req.post('http://localhost:5000/home', data = {'statu': stu})
            else:
                std = s[0] + " is down"
                req.post('http://localhost:5000/home', data = {'statd': std})
        
        statfile.close()
        time.sleep(30)

if __name__ == "__main__":
    print("Username/password for webapp")
    usr = input("Username: ")
    passw = getpass.getpass("Password: ")
    service_check(usr, passw)

