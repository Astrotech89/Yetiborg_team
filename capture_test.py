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
frameRate = 30                        # Camera image capture frame rate

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




try: 
    camera = picamera.PiCamera()
    camera.resolution = (imageHeight, imageWidth)
    camera.framerate = frameRate

    capture = picamera.array.PiRGBArray(camera, size=(imageHeight, imageWidth))
    time.sleep(0.1)


    try:
        camera.capture(capture, format="bgr")
        image = capture.array
        # Save image in txt. Might need to be saved as image[:][:][0], not sure.
        try:
            np.savetxt('raw_image.txt', image[:,:,0])
        except:
            pass
        # Save image as PNG and as JPEG to check the difference in color encoding.
        cv2.imwrite('./raw_capture_png.png', image)
        cv2.imwrite('./raw_capture_jpeg.jpeg', image)

        # Delete the current image
        capture.truncate(0)
    except: 
        print "Damn, capture didn't work"
        pass

    try:
        # Trying continuous capture
        for frame in camera.capture_continuous(capture, format="bgr", use_video_port=True):
            new_image_continuous = frame.array
            # Save image frmo continuous capture with bhr format
            cv2.imwrite('./capture_from_continuous.jpeg', new_image_continuous)
            capture.truncate(0)
            break
    except: 
        print "Shit, continuous didn't work"
        pass

    try:
        # Trying sequence capture
        for frame in camera.capture_sequence(capture, format="bgr", use_video_port=True):
            new_image_sequence = frame.array
            # Save image frmo continuous capture with bhr format
            cv2.imwrite('./capture_from_sequence.jpeg', new_image_sequence)
            capture.truncate(0)
            break
    except: 
        print "Bollocks, sequence didn't work"
        pass



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

del camera
ZB.SetLed(False)
print 'Program terminated'