#!/usr/bin/python3
import sys
import os
import pika
import mysql.connector
import time
import datetime
from tabulate import tabulate
import requests
import getpass

#Time stuff
tm = time.strftime('%Y-%m-%d') # Time for SQL timestamp
mo = time.strftime('%Y-%m') # Time for monthly price calc
mof = (mo + "%") # Time for monthly price calc formatted
dat = datetime.datetime.now()
monthd = dat.strftime("%B") # Day of month

#RabbitMQ connection
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='bc')

#Session to webapp
print("Username/password for webapp")
username = input("Username: ")
password = getpass.getpass("Password: ")
s = requests.session()
r = s.post('http://localhost:5000/login', data={'username': username, 'password': password})
#print(r.text)

#Barcode scanner and translator
def sc():
	
	#MySQL creds
	connection = mysql.connector.connect(
		host='localhost',
		database='bc_db',
		user='admin',
		password='sqlpass'
	)

	#Creddit to 'brechmos' on https://www.raspberrypi.org/forums/viewtopic.php?f=45&t=55100
	#for creating the translation code
	hid = { 4: 'a', 5: 'b', 6: 'c', 7: 'd', 8: 'e', 9: 'f', 10: 'g', 11: 'h', 12: 'i', 13: 'j', 14: 'k', 15: 'l', 16: 'm', 17: 'n', 18: 'o', 19: 'p', 20: 'q', 21: 'r', 22: 's', 23: 't', 24: 'u', 25: 'v', 26: 'w', 27: 'x', 28: 'y', 29: 'z', 30: '1', 31: '2', 32: '3', 33: '4', 34: '5', 35: '6', 36: '7', 37: '8', 38: '9', 39: '0', 44: ' ', 45: '-', 46: '=', 47: '[', 48: ']', 49: '\\', 51: ';' , 52: '\'', 53: '~', 54: ',', 55: '.', 56: '/' }

	hid2 = { 4: 'A', 5: 'B', 6: 'C', 7: 'D', 8: 'E', 9: 'F', 10: 'G', 11: 'H', 12: 'I', 13: 'J', 14: 'K', 15: 'L', 16: 'M', 17: 'N', 18: 'O', 19: 'P', 20: 'Q', 21: 'R', 22: 'S', 23: 'T', 24: 'U', 25: 'V', 26: 'W', 27: 'X', 28: 'Y', 29: 'Z', 30: '!', 31: '@', 32: '#', 33: '$', 34: '%', 35: '^', 36: '&', 37: '*', 38: '(', 39: ')', 44: ' ', 45: '_', 46: '+', 47: '{', 48: '}', 49: '|', 51: ':' , 52: '"', 53: '~', 54: '<', 55: '>', 56: '?'  }
	############

	device = open('/dev/hidraw4') #The HID(scanner)

	while True: 
		
		#Cursor for SQL
		cursor = connection.cursor()
		
		#Get and Calculate price of item database
		cursor.execute("SELECT Price FROM bc_store")
		pquery = cursor.fetchall()
		price = 0
		for row in pquery:
			price += row[0]
		print("# " + str(price) + ":- total value of database #")

		#Get and Calculate montly expense
		cursor.execute("SELECT Price FROM bc_hist WHERE Date LIKE %s", (mof,))
		pquery = cursor.fetchall()
		mprice = 0
		for row in pquery:
			mprice += row[0]
		print("# " + str(mprice) + ":- total this month" + " (" + monthd + ")"+ "  #")

		print("#####################################\n")
		
		log = open('barcode.log', 'a+')
		
		#Creddit to 'brechmos' on https://www.raspberrypi.org/forums/viewtopic.php?f=45&t=55100
		#for creating the translation code
		#########
		bc = ""
		shift = False
		done = False
		while not done:
			
			buffer = device.read(8)
			for c in buffer:
				if int(ord(c)) > 1:
					
					# 40 at end of barcode means end of barcode
					if int(ord(c)) == 40:
						done = True
						break
					
					# If c = 2, means shift key, use hid2
					if shift:
						if int(ord(c)) == 2:
							shift = True
						else:
							bc += hid2[ord(c)]
							shift = False
							
					# if not shifted, use hid
					else:
						if int(ord(c)) == 2:
							shift = True
							
						else:
							bc += hid[ord(c)]
		#########

		#Query sql table
		cursor.execute("SELECT * FROM bc_store WHERE Barcode =%s LIMIT 1", (bc,))
		result = cursor.fetchall()
		tbl = (tabulate(result, headers=['id', 'Barcode', 'ProductName', 'ProductType', 'Price'], tablefmt='psql'))
		
		#If item doenst exist in table
		if not result:

			#New item Info
			print("### New item! ###")
			Pname = input("Product Name: ")
			Ptype = input("Product Type: ")
			Price = input("Price: ")

			#Insert info into product database
			cursor.execute("INSERT INTO bc_store (Barcode, ProductName, ProductType, Price) VALUES (%s, %s, %s, %s)", (bc, Pname, Ptype, Price))
			print("\n")
			print("### Item added! ###")

			#Ad to history database
			cursor.execute("INSERT INTO bc_hist (Barcode, ProductName, ProductType, Price, Date) VALUES (%s, %s, %s, %s, %s)", (bc, Pname, Ptype, Price, tm))

			#Query table, print info
			cursor.execute("SELECT * FROM bc_store WHERE Barcode =%s LIMIT 1", (bc,))
			nresult = cursor.fetchall()
			tbl = (tabulate(nresult, headers=['id', 'Barcode', 'ProductName', 'ProductType', 'Price'], tablefmt='psql'))

			bc_result = []
			for row in nresult:
				bc_result.append(row)
				#print(row)
			
			ntbl = (tabulate(nresult, headers=['id', 'Barcode', 'ProductName', 'ProductType', 'Price'], tablefmt='psql'))
			print(ntbl)

		#If item exists in table
		else:		
			
			#Post barcode to webserver
			s.post('http://localhost:5000/home', data = {'Bcode': bc})

			#Print tabulate table
			print(tbl)
			
			#Insert into history stable
			#cursor.execute("INSERT INTO bc_hist (Barcode, ProductName, ProductType, Price, Date) SELECT Barcode, ProductName, ProductType, Price, %s FROM bc_store WHERE bc_store.Barcode =%s", (tm, bc))
			
			#Print existing info in table
			bc_result = []
			for row in result:
				bc_result.append(row)
				#print(row)

		connection.commit() #Commit sql changes
		log.flush() #Flush internal buffer
		os.fsync(log.fileno())
		log.write(str(bc_result) + '\n') #Log 'em 
		log.write(tbl + '\n')
		log.close() 
		print ("\n")
		print("#####################################")
		print("# " + "Barcode: " + bc + "            #") #Print Barcode
	
sc()
#Callback function called by RabbitMQ
def callback(ch, method, proprties, body):
	print('+++ Call recieved from webapp')
	if body == "Run":
		print('+++ Starting scanner')
		sc()

#Consumer for RabbitMQ
channel.basic_consume(queue='bc', on_message_callback=callback, auto_ack=True)
print('+++ Waiting to start scanner')
channel.start_consuming()



	