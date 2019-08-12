#!/usr/bin/python3
import getpass
from check_service import service_check
import subprocess
import time

print("Username/password for webapp")
usr = input("Username: ")
passw = getpass.getpass("Password: ")

subprocess.Popen(['konsole', '-e', 'python3 webapp.py'])
time.sleep(3)
service_check(usr, passw)
