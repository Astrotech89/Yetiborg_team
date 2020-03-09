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
import numpy



#Globals
global camera
global ZB
global processor
# global motionDetected
global running 
running = True


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
	def __init__(self):
		super(MoveYB, self).__init__()
		self.stream = picamera.array.PiRGBArray(camera)

	def ConstantVelocity(self,driveLeft,driveRight):
		ZB.SetMotor1(-maxPower * driveRight)
		ZB.SetMotor2(-maxPower * driveRight)
		ZB.SetMotor3(-maxPower * driveLeft)
		ZB.SetMotor4(-maxPower * driveLeft)

	def ProcesImage(self, image):
		#Image processing code here
		if flippedImage:
			image = cv2.flip(image, -1)
		if self.lastImage is None:
			self.lastImage = image.copy()
			return
		



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
capture = StreamInit()