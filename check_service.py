#!/usr/bin/python3
import socket
import time
import requests


def service_check():
    def check_service(ip, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ch = sock.connect_ex((ip, port))
        sock.close()
        return ch

    services = [
        ("DNS", '192.168.1.82', 53),
        ("DNS_Web", '192.168.1.82', 80),
        ("DNS_SSH", '192.168.1.82', 22),
        ("SMB", '192.168.1.121', 139),
        ("SMB_SSH", '192.168.1.121', 22),
    ]
    req = requests.session()
    while True:
        for s in services:
            check = check_service(s[1], s[2])
            print("%s is %s" % (s[0], "up" if check == 0 else "down"))
        
            if check == 0:
                stu = s[0] + " is up"
                req.post('http://localhost:5000/home/services', data = {'statu': stu})
            else:
                std = s[0] + " is down"
                req.post('http://localhost:5000/home/services', data = {'statd': std})
        time.sleep(30)

if __name__ == "__main__":
    service_check()
