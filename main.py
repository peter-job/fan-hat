#!/usr/bin/python
# -*- coding:utf-8 -*-

from drivers.SSD1306 import SSD1306
from drivers.PCA9685 import PCA9685
from datetime import datetime
import time
import traceback
import socket
import threading
import requests
import os
from PIL import Image,ImageDraw,ImageFont
import psutil
from enum import Enum

def getIp(ipVersion):
	ip = ""
	if ipVersion == IpVersion.Public:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(('8.8.8.8', 80))
		ip = s.getsockname()[0]
	elif ipVersion == IpVersion.Internal:
		ip = requests.get('https://checkip.amazonaws.com').text.strip()
	return ip

def toggleIpVersion(ipVersion):
	if ipVersion == IpVersion.Public:
		ipVersion =IpVersion.Internal
	elif ipVersion == IpVersion.Internal:
		ipVersion = IpVersion.Public
	return ipVersion

class IpVersion(Enum):
	Public = 1
	Internal = 2

print("""
C A R D B O A R D   C A F E
---- fan hat & display ----
""")

try:
	PATH = os.path.dirname(__file__)

	oled = SSD1306()

	pwm = PCA9685(0x40, debug=False)
	pwm.setPWMFreq(50)
	pwm.setServoPulse(0,100)
	
	# Initialize library.
	oled.Init()
	oled.ClearBlack()

	# Create blank image for drawing.
	image1 = Image.new('1', (oled.width, oled.height), "WHITE")
	draw = ImageDraw.Draw(image1)
	font = ImageFont.truetype(os.path.join(PATH, "resources/gohufont-11.ttf"), 11)

	ipVersion = IpVersion.Public
	ip = getIp(ipVersion)
	ticks = 0
	while(1):
		draw.rectangle((0,0,128,32), fill = 1)

		# get ip
		if ticks % 4 == 0:
			ipVersion = toggleIpVersion(ipVersion)
			ip = getIp(ipVersion)
		draw.text((0,0), "IP:", font=font, fill = 0)
		draw.text((20,0), ip, font=font, fill = 0)

		# get temp
		draw.text((0,16), "T:", font=font, fill = 0)

		file = open("/sys/class/thermal/thermal_zone0/temp")  
		temp = float(file.read()) / 1000.00  
		temp = float('%.1f' % temp)
		file.close()
		draw.text((14,16), str(temp), font=font, fill = 0)
				
		# get cpu usage
		draw.text((46,16), "C:", font=font, fill = 0)
		cpu = psutil.cpu_percent()
		draw.text((60,16), str(cpu), font=font, fill = 0)

		# get ram usage
		draw.text((90, 16), "M:", font=font, fill = 0)
		ram = psutil.virtual_memory().percent
		draw.text((105,16), str(ram), font=font, fill = 0)

		# if(temp > 40):
		# 	pwm.setServoPulse(0,40)
		if(temp > 50):
			pwm.setServoPulse(0,50)
		elif(temp > 55):
			pwm.setServoPulse(0,75)
		elif(temp > 60):
			pwm.setServoPulse(0,90)
		elif(temp > 65):
			pwm.setServoPulse(0,100)
		else:
			pwm.setServoPulse(0,0)
		#show
		oled.ShowImage(oled.getbuffer(image1.rotate(180)))

		#log
		if ticks % 300 == 0:
			ticks = 0
			publicIp = getIp(IpVersion.Public)
			privateIp = getIp(IpVersion.Internal)
			now = datetime.now()
			current_time = now.strftime("%I:%M %p")
			print("fan HAT update @ %s" %current_time)
			print("public ip:   %s" %publicIp)
			print("private ip:  %s" %privateIp)
			print("temperature: %.1f" %temp)
			print("ram usage:   %s" %str(ram))
			print("cpu usage:   %s" %str(cpu))
			print("\n")

		#sleep
		time.sleep(1)
		ticks += 1
		


except IOError as e:
    oled.Closebus()
    print(e)
    
except KeyboardInterrupt:    
    print("ctrl + c:")
    oled.Closebus()
