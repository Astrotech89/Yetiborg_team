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
import support_functions as spf 

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

# Power settings
voltageIn = 8.4                         # Total battery voltage to the ZeroBorg (change to 9V if using a non-rechargeable battery)
voltageOut = 6.0                        # Maximum motor voltage

# Camera settings
imageWidth  = 320                       # Camera image width
imageHeight = 240                       # Camera image height
frameRate = 10                          # Camera image capture frame rate

# Auto drive settings
autoZoneCount = 80                      # Number of detection zones, higher is more accurate
autoMinimumMovement = 20                # Minimum movement detection before driving
steeringGain = 4.0                      # Use to increase or decrease the amount of steering used
flippedImage = True                     # True if the camera needs to be rotated
showDebug = True                        # True to display detection values

# Setup the power limits
if voltageOut > voltageIn:
	maxPower = 1.0
else:
	maxPower = voltageOut / float(voltageIn)


class MoveYB(threading.Thread):
	# print 'imported class'
	def __init__(self):
		super(MoveYB, self).__init__()
		self.stream = picamera.array.PiRGBArray(camera)
		self.event = threading.Event()
		self.start()

	# print 'import after init'
	def Power_Change(self, steering_angle):
		distance_between_opposite_wheels = 14.5 /100. #m
		diameter_of_wheel = 6.5/100. #m
		intergration_time = 350./1000. #sec, TBD
		w = np.abs(steering_angle) * distance_between_opposite_wheels / diameter_of_wheel / intergration_time
		power_ratio = 1. - w/300
		return power_ratio

	
	# ---------------------steering_angle calculation------------------------
	# steering_angle = 200
	# ---------------------steering_angle calculation------------------------


	def Turn_YB(self,steering_angle):
		# global motion
		# global ZB
		# global maxPower
		# global steering_angle
		# motion = True
		power_ratio = self.Power_Change(steering_angle)
		print 'power = ', power_ratio
		print 'Max Power = ', maxPower

		# Turn Right
		if steering_angle > 0:
			# while steering_angle > 0:
			print 'turning right'
			ZB.SetMotor1(-maxPower * power_ratio)
			ZB.SetMotor2(-maxPower * power_ratio)
			ZB.SetMotor3(-maxPower)
			ZB.SetMotor4(-maxPower)
			print ZB.GetMotor1()
			print ZB.GetMotor2()
			print ZB.GetMotor3()
			print ZB.GetMotor4()


		# Turn Left
		elif steering_angle < 0:
			# while steering_angle < 0:
			print 'turning left'
			ZB.SetMotor1(-maxPower)
			ZB.SetMotor2(-maxPower)
			ZB.SetMotor3(-power_ratio * maxPower)
			ZB.SetMotor4(-power_ratio * maxPower)
			print ZB.GetMotor1()
			print ZB.GetMotor2()
			print ZB.GetMotor3()
			print ZB.GetMotor4()
		
		else:
			# while steering_angle == 0:
			print 'going towards god'
			ZB.SetMotor1(-maxPower)
			ZB.SetMotor2(-maxPower)
			ZB.SetMotor3(-maxPower)
			ZB.SetMotor4(-maxPower)
			print ZB.GetMotor1()
			print ZB.GetMotor2()
			print ZB.GetMotor3()
			print ZB.GetMotor4()
				# print ZB.SetMotor1(-maxPower)
				# ZB.SetLed(True)
		return
	
	

	def ProcesImage(self, image):
		#Image processing code here
		if flippedImage:
			image = cv2.flip(image, -1)
		if self.lastImage is None:
			self.lastImage = image.copy()



	# def Lane_Detection():
		


class StreamInit(threading.Thread):
	def __init__(self):
		super(StreamInit, self).__init__()
		self.start()

	def run(self):
		global camera
		global processor
		camera.capture_sequence(self.TriggerStream(), format='rgb', use_video_port=True)
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
camera.framerate = frameRate
imageCenterX = imageWidth / 2.0
imageCenterY = imageHeight / 2.0

print 'Setup stream processing thread'

processor = MoveYB()
print 'Processor imported'
# time.sleep(2)
capture = StreamInit()
print 'capture imported'



testing = True
if testing:
	try:
		print 'begin testing'
		# time.sleep(2)
		processor.Turn_YB(30)
		# time.sleep(2.0)
		processor.Turn_YB(20)
		# time.sleep(5.0)
		# processor.Turn_YB(-20)
		# time.sleep(5.)
		# processor.Turn_YB(-30)
		# time.sleep(5.)
	except KeyboardInterrupt:
		print '\nUser shutdown testing'
		ZB.MotorsOff()
	except:
		e = sys.exc_info()
		print
		print e
		print '\nUnexpected error, shutting down testing!'
		ZB.MotorsOff()


try:
	# ZB.MotorsOff()
	while running:
		# ZB.SetLed(motion)
		time.sleep(0.01)
		
	# ZB.MotorsOff()
except KeyboardInterrupt:
	print '\nUser shutdown'
	ZB.MotorsOff()
except:
	e = sys.exc_info()[0]
	print
	print e
	print '\nUnexpected error, shutting down!'
	ZB.MotorsOff()
running = False
capture.join()
processor.terminated = True
processor.join()
del camera
ZB.SetLed(False)
print 'Program terminated'