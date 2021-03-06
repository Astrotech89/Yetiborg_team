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

#Custom imports
import new_single_line_support_functions as spf 


sys.stdout = sys.stderr
print 'Libraries loaded'

#Globals
global camera
global ZB
global processor
global running 
# global steering_angle
# global maxPower
running = True
# motion = False



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
failsafe = True
for i in range(5):
	ZB.SetCommsFailsafe(True)
	failsafe = ZB.GetCommsFailsafe()
	if failsafe:
		break
if not failsafe:
	print 'Board %02X failed to report in failsafe mode!' % (ZB.i2cAddress)
	sys.exit()
ZB.ResetEpo()

# Power settings
voltageIn = 8.4                         # Total battery voltage to the ZeroBorg (change to 9V if using a non-rechargeable battery)
voltageOut = 6.0                        # Maximum motor voltage

# Camera settings
imageWidth  = 320                       # Camera image width
imageHeight = 240                       # Camera image height
frameRate = 25                  # Camera image capture frame rate

# Auto drive settings
autoZoneCount = 80                      # Number of detection zones, higher is more accurate
autoMinimumMovement = 20                # Minimum movement detection before driving
steeringGain = 4.0                      # Use to increase or decrease the amount of steering used
flippedImage = False                     # True if the camera needs to be rotated
showDebug = True                        # True to display detection values

# Setup the power limits
if voltageOut > voltageIn:
	maxPower = 1.0
else:
	# maxPower = voltageOut / float(voltageIn)
	maxPower = 0.55

	#Motors 1 & 2 are on the right

def moveStart(Power):
	ZB.SetMotor1(-Power)
	ZB.SetMotor2(-Power)
	ZB.SetMotor3(Power)
	ZB.SetMotor4(Power)


class MoveYB(threading.Thread):
	# print 'imported class'
	def __init__(self):
		super(MoveYB, self).__init__()
		self.stream = picamera.array.PiRGBArray(camera)
		self.event = threading.Event()
		self.terminated = False
		self.start()

	def run(self):
	# This method runs in a separate thread
		while not self.terminated:
			# Wait for an image to be written to the stream
			if self.event.wait(1):
				try:
					# Read the image and do some processing on it
					self.stream.seek(0)
					self.steering_angle, self.relative_distance_from_center = self.ProcessImage(self.stream.array)
					self.Turn_YB()

				finally:
					# Reset the stream and event
					self.stream.seek(0)
					self.stream.truncate()
					self.event.clear()
	
	
	def ProcessImage(self, image):
		#Image processing code here
		if flippedImage:
			image = cv2.flip(image, -1)
		# if self.lastImage is None:
		# 	self.lastImage = image.copy()
		
		steering_angle, relative_distance_from_center =  spf.auto_guide(image, color="white")
		# cv2.imshow('output',masked_image)
		# print(camera.framerate)	


		return -steering_angle, relative_distance_from_center


	# def Power_Change(self):
	# 	distance_between_opposite_wheels = 14.5 /100. #m
	# 	diameter_of_wheel = 6.5/100. #m
	# 	intergration_time = 350./1000. #sec, TBD
	# 	w = np.abs(self.steering_angle) * distance_between_opposite_wheels / diameter_of_wheel / intergration_time
	# 	power_ratio = 1. - w/300
	# 	return np.abs(power_ratio)

	def Power_Change(self):

		# distance_between_opposite_wheels = 14.5 /100. #m
		# diameter_of_wheel = 6.5/100. #m
		# intergration_time = 15./1000. #sec, TBD
		# w = np.abs(self.steering_angle) * distance_between_opposite_wheels / diameter_of_wheel / intergration_time
		# power_ratio_angle = np.abs(1. - w/300)


		power_ratio_angle = self.steering_angle/90.
		if np.abs(self.relative_distance_from_center) > 1:
			power_ratio_distance = 1
		else:
			power_ratio_distance = np.abs(self.relative_distance_from_center)
			
		total_power_ratio = np.sqrt(power_ratio_angle**2 + power_ratio_distance**2)/2
		# total_power_ratio = power_ratio_distance
		if np.abs(self.steering_angle) < 15:
			total_power_ratio = 0.65 * total_power_ratio
		elif  15 <= np.abs(self.steering_angle) < 35:
			total_power_ratio = 1.5 * total_power_ratio
		else:
			total_power_ratio = 1.8 * total_power_ratio

		print('total power ration = ', total_power_ratio)
			

		return total_power_ratio


    	

	def Turn_YB(self):
		# global motion
		# global ZB
		# global maxPower
		# global steering_angle
		# motion = True
		# buffer = 30.
		power_ratio = self.Power_Change()
		if power_ratio >=1.:
			power_ratio = 1.0
		# print 'power = ', power_ratio
		# print 'Max Power = ', maxPower
		# steering_angle = self.ProcessImage


		# Turn Right
		if self.steering_angle > 0:
			print self.steering_angle
			print 'turning left'
			ZB.SetMotor1(-maxPower)
			ZB.SetMotor2(-maxPower)
			ZB.SetMotor3(-maxPower * power_ratio)
			ZB.SetMotor4(-maxPower * power_ratio)
			return


		# Turn Left
		elif self.steering_angle < 0:
			print self.steering_angle
			print 'turning right'
			ZB.SetMotor1(-maxPower * power_ratio)
			ZB.SetMotor2(-maxPower * power_ratio)
			ZB.SetMotor3(-maxPower)
			ZB.SetMotor4(-maxPower)
			return

		
		elif self.steering_angle==0:
			if self.relative_distance_from_center < 0.2:
				print 'turning right relative distance'
				ZB.SetMotor1(-maxPower * power_ratio)
				ZB.SetMotor2(-maxPower * power_ratio)
				ZB.SetMotor3(-maxPower)
				ZB.SetMotor4(-maxPower)

			elif self.relative_distance_from_center > 0.2:
				print 'turning left relative distance'
				ZB.SetMotor1(-maxPower)
				ZB.SetMotor2(-maxPower)
				ZB.SetMotor3(-maxPower * power_ratio)
				ZB.SetMotor4(-maxPower * power_ratio)
		else:
			print self.steering_angle
			print 'going towards god'
			ZB.SetMotor1(-maxPower)
			ZB.SetMotor2(-maxPower)
			ZB.SetMotor3(-maxPower)
			ZB.SetMotor4(-maxPower)
			return
		


class StreamInit(threading.Thread):
	def __init__(self):
		super(StreamInit, self).__init__()
		self.start()

	def run(self):
		global camera
		global processor
		camera.capture_sequence(self.TriggerStream(), format='bgr', use_video_port=True)
		print 'Terminating stream'
		processor.terminated = True
		processor.join()
		print 'Stream Terminated'

	def TriggerStream(self):
		global running
		while running:
			if processor.event.is_set():
				time.sleep(0.01)
			else:
				yield processor.stream
				processor.event.set()


#Run Sequence
print 'Camera Setup'
camera = picamera.PiCamera()
camera.resolution = (imageWidth,imageHeight)
# camera.framerate = frameRate
imageCenterX = imageWidth / 2.0
imageCenterY = imageHeight / 2.0


print 'Setup stream processing thread'

start = raw_input('Perform start turn? ')
if start == 'y':
	moveStart(-0.40)



try:
	processor = MoveYB()
	print 'Processor imported'
	time.sleep(2)
	capture = StreamInit()
	print 'capture imported'



# testing = False
# if testing:
# 	try:
# 		print 'begin testing'
# 		processor = MoveYB()
# 	except KeyboardInterrupt:
# 		print '\nUser shutdown testing'
# 		ZB.MotorsOff()
# 	except:
# 		e = sys.exc_info()
# 		print
# 		print e
# 		print '\nUnexpected error, shutting down testing!'
# 		ZB.MotorsOff()



	# ZB.MotorsOff()
	while running:
		ZB.SetLed(True)
		time.sleep(0.01)
		
	# ZB.MotorsOff()
except KeyboardInterrupt:
	print '\nUser shutdown'
	processor.terminated = True
	running = False
	ZB.MotorsOff()
except:
	e = sys.exc_info()[0]
	print
	print e
	print '\nUnexpected error, shutting down!'
	ZB.MotorsOff()
	
# running = False
capture.join()
# processor.terminated = True
processor.join()
del camera
ZB.SetLed(False)
print 'Program terminated'