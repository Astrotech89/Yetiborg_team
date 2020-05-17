#!/usr/bin/env python
# coding: Latin-1

# Load library functions we want
import time
import os
import sys
import ZeroBorg
import io
import threading
import picamera
import picamera.array
import cv2
import numpy as np

import new_single_line_support_functions as spf
import support_functions as spf2

sys.stdout == sys.stderr
print 'Libraries loaded'

# Setup the ZeroBorg
ZB = ZeroBorg.ZeroBorg()
#ZB.i2cAddress = 0x44                  # Uncomment and change the value if you have changed the board address
ZB.Init()
#Safety stuff
if not ZB.foundChip:
	boards = ZeroBorg.ScanForZeroBorg()
	if len(boards) == 0:
		print 'No ZeroBorg found, check you are attached :)'
	else:
		print 'No ZeroBorg at address %02X, but we did find boards:' % (ZB.i2cAddress)
		for board in boards:
			print '    %02X (%d)' % (board, board)
		print 'If you need to change the I�C address change the setup line so it is correct, e.g.'
		print 'ZB.i2cAddress = 0x%02X' % (boards[0])
	sys.exit()
#ZB.SetEpoIgnore(True)                 # Uncomment to disable EPO latch, needed if you do not have a switch / jumper
# Ensure the communications failsafe has been enabled!
failsafe = False
for i in range(5):
	ZB.SetCommsFailsafe(True)
	failsafe = ZB.GetCommsFailsafe()
	if failsafe:
		break
if not failsafe:
	print 'Board %02X failed to report in failsafe mode!' % (ZB.i2cAddress)
	sys.exit()
ZB.ResetEpo()

camera = picamera.PiCamera()
camera.resolution = (320,240)
camera.rotation=180
camera.framerate = 30
rawCapture = picamera.array.PiRGBArray(camera, size=(320,240))
time.sleep(0.1)
# ZB.SetLed(True)


for frame in camera.capture_continuous(rawCapture,format='bgr',use_video_port=True):
	image = frame.array
	image2 = cv2.cvtColor(image, cv2.COLOR_BGR2HLS)
	# img = cv2.cvtColor(image, cv2.COLOR_BGR2HLS)
	mask_image, mask = spf.mask_color(image2,color='white')
	# print(np.max(mask_image))
	# print(np.shape(mask_image))
	
	steering_angle, _, x_min, y_min, x_max, y_max, flag = spf.steering_angle_calculation(image2, color='white',value_threshold=170)
	height, width, _ = image.shape

	# print(relative_distance_from_center)
	# kernel = np.ones((3,3), np.uint8)
	# mask = cv2.erode(mask, kernel,iterations=6)
	# mask = cv2.dilate(mask,kernel,iterations=10)
	# contours, somethingelse = cv2.findContours(mask.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
	# cv2.drawContours(mask_image,contours,-1,(0,255,0),3)
	# if len(contours) > 0:
	# 	x,y,w,h = cv2.boundingRect(contours[0])
	# 	cv2.rectangle(mask_image, (x,y),(x+w,y+h), (0,0,255),3)
	# img = np.zeros((height, width, 3), np.uint8)
	# img[x_max, y_max] = [0,0,255]
	# img[x_min, y_min] = [0,255,0]
	# cv2.imshow("point", img)
	blue = [0,0,0]
	red = [0,0,0]
	green = [0,0,0]
	try:
		if flag:
			cv2.circle(mask_image, (int(y_min),int(x_min)), 10, red, -1)
			cv2.circle(mask_image, (int(y_max),int(x_max)), 10, blue, -1)
			cv2.circle(mask_image, (int((y_min+y_max)/2), int((x_min+x_max)/2)), 10, green, -1)
			

		else:
			cv2.circle(mask_image, (int(x_min),int(y_min)), 10, red, -1)
			cv2.circle(mask_image, (int(x_max),int(y_max)), 10, blue, -1)
			cv2.circle(mask_image, (int((x_min+x_max)/2), int((y_min+y_max)/2)), 10, green, -1)
	except:
		pass

	cv2.imshow("Original",mask_image)
	rawCapture.truncate(0)
	key = cv2.waitKey(1) & 0xFF
	if key == ord("q"):
		break

del camera
ZB.SetLed(False)
print 'Terminated'
