import serial, threading
from time import sleep, ctime, localtime, strftime
from flask import Flask, request, redirect

print('>>Start!') 
while True:
	try:
		s = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, timeout=90)
		break
	except:
		sleep(1)
		print('>>>Serial Port Error')
		pass
########################################
#Static Values for voltage based control 
bat_on = 12.5
bat_off = 11.9
########################################
# Manual Control Timeout -  Minutes
man_timeout = 30 
########################################

timestamp = localtime()
bat = 0.0
pnl = 0.0
stat = 0
flagAuto = True
man_counter = man_timeout
man_countsg = 0
man_action = 0

def manualcounter():
	global flagAuto, man_counter, man_countsg, man_timeout
	while True:
		if not(flagAuto):
			if man_countsg>0:
				man_countsg = man_countsg - 1
			else:
				if man_counter>0:
					man_counter = man_counter - 1
					man_countsg = 59
				else:
					flagAuto=True
					man_counter=man_timeout
					man_countsg=0
		sleep(1) 

def httpBatt(timestamp, bat, pnl, stat, flagAuto):
	global bat_on,bat_off,man_counter,man_timeout
	return """
	<!DOCTYPE html>
	<html lang="en-us">
		<head>
		<title>Mandor Link</title>
		<meta http-equiv="refresh" content="10"> 
		<meta name="viewport" content="width=device-width, initial-scale=1.0">
		</head>
		<body style="background-color:black">
			<center>
			<font color="lime">
				<h1> Link Data </h1> 
				<h3><font color="green">Now: %s</font><h3>
				
				<h2>
					Last Tx: %s
					<br>
					Battery: %2.1f
					<br>
					Panel: %2.1f
					<br>
					Status: %s
				</h2>
			</font>
			<h3>
				<font color="green">
					LinkOn: %2.1f
					<br>
					LinkOff: %2.1f
					<br>
					Control: %s
					<br>
					<br>
					<form action="on" method="post">
		         	<button style="color:green;background-color:black;border:1px solid #336600;padding:10px">
    				On</button>
    				</form>
    				<br>
					<form action="off" method="post">
		         	<button style="color:green;background-color:black;border:1px solid #336600;padding:10px">
    				Off</button>
    				</form>
    				<br>
    				%s
			</h3>
			</center>
		</body>
	</html>
	
	"""%(strftime("%d %b %Y %H:%M", localtime()),
		strftime("%d %b %Y %H:%M", timestamp), 
		bat, pnl, 
		'On' if stat == 1 else 'Off',
		bat_on, bat_off,
		'Auto' if flagAuto else 'Manual',
		' ' if flagAuto else '%02d:%02d'%(man_counter,man_countsg) 
		)

def saveBattRecord(timestamp, bat, pnl, stat):
	battdir='/home/fx/Escritorio/'
	battfile = battdir + 'batteryRecord.csv'
	battObj = open(battfile, 'a')
	timedata = strftime("%d %b %Y %H:%M", timestamp)
	battObj.write('%s,%2.1f,%2.1f,%d\n'%(timedata, bat, pnl, stat))
	battObj.close() 

def RFControl():
	global bat, pnl, stat, timestamp, man_action, flagAuto
	command_on = '@ON\n'.encode()
	command_off = '@OFF\n'.encode()

	
	while True:
		try:
			data = ''
			data = str(s.readline())
			if ',' in data:
				data = data.replace("b'","")	
				data = data.replace("\\r\\n'","")	 
		
				data = data.split(',')
				if len(data)==3:
					bat = float(data[0])
					pnl = float(data[1])
					stat = int(data[2])
					timestamp = localtime()
					print (strftime("%d/%m/%Y - %H:%M", timestamp), bat, pnl, stat)
					saveBattRecord(timestamp,bat,pnl,stat)

					if flagAuto:	
						if (bat<bat_off) and (stat == 1):
							s.write(command_off)
			
						if (bat>bat_on) and (stat == 0):
							s.write(command_on)
					else:
						if man_action != stat:
							if man_action==0:
								s.write(command_off) 
							if man_action==1:
								s.write(command_on) 

		except:
			print('>>>Error!') 			
			pass

threading.Thread(target=RFControl).start()
threading.Thread(target=manualcounter).start()

print('>>>Go!')

app = Flask(__name__)

@app.route('/on', methods=['GET', 'POST'])
def on():
	global flagAuto, man_counter, man_countsg, man_action
	flagAuto = False
	man_action = 1
	man_counter = man_timeout
	man_countsg = 59	
	return redirect("/")

@app.route('/off', methods=['GET', 'POST'])
def off():
	global flagAuto, man_counter, man_countsg, man_action
	flagAuto = False
	man_action = 0
	man_counter = man_timeout
	man_countsg = 59	
	return redirect("/")

@app.route('/', methods=['GET', 'POST'])
def home():
	global bat, pnl, stat, timestamp, flagAuto	
	return httpBatt(timestamp, bat, pnl, stat, flagAuto)

if __name__ == '__main__':
	app.run(host='0.0.0.0', port='80')