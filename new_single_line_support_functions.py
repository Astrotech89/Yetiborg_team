#!/usr/bin/env python
# coding: Latin-1

import cv2
import numpy as np 


def mask_color(frame, color):

<<<<<<< HEAD
    white = [[70, 10, 155], [255, 255, 255]]
=======
    white = [[70, 10, 150], [255, 255, 255]]
>>>>>>> code_fixing
    orange = [[1, 10, 60], [15, 200, 220]]

    if color=='white':

        lower = np.array(white[0])
        upper = np.array(white[1])

    elif color=='orange':
        lower = np.array(orange[0])
        upper = np.array(orange[1])
        

    mask = cv2.inRange(frame, lower ,upper)
    output = cv2.bitwise_and(frame, frame, mask = mask)

    return output


def steering_angle_calculation(frame, color):
    
    masked_image = mask_color(frame, color=color)
    sums = np.sum(masked_image, axis=2)
    height, width = sums.shape

    try:
        (y,x)=np.where(sums>200)
        # x_max = np.max(x[np.where(y==np.min(y))])
        # x_min = np.max(x[np.where(y==np.max(y))])
        y_max = np.max(y)
        y_min = np.min(y)

        x_min_median = np.median(x[np.where(y==np.min(y))])
        x_max_median = np.median(x[np.where(y==np.max(y))])





        y_middle_calc_line = (y_min + y_max)/2
        x_middle_calc_line = (x_min_median + x_max_median)/2

        y_middle_line = height/2
        x_middle_line = width/2
        
        if x_middle_calc_line - x_middle_line < 0:
            distance_from_center = -np.sqrt((x_middle_calc_line - x_middle_line)**2 + (y_middle_calc_line - y_middle_line)**2)
        if x_middle_calc_line - x_middle_line >= 0:
            distance_from_center = np.sqrt((x_middle_calc_line - x_middle_line)**2 + (y_middle_calc_line - y_middle_line)**2)
        

        relative_distance_from_center = distance_from_center / (width/2)
        # print("relative distance from center", relative_distance_from_center)
            

        if x_min_median != x_max_median:
            steering_angle = np.rad2deg(-np.arctan((y_min - y_max)/(x_min_median - x_max_median)))
        else:
            steering_angle = 0

        if steering_angle < 0:
            corr_steering_angle = -(steering_angle + 90)
        if steering_angle > 0:
            corr_steering_angle = 90 - steering_angle
        else:
            corr_steering_angle = 0

    except:
        print("no line detected")
        corr_steering_angle = 0
        relative_distance_from_center = 0
    
    
    
    return corr_steering_angle, relative_distance_from_center






def Power_Change(steering_angle, relative_distance_from_center):

    distance_between_opposite_wheels = 14.5 /100. #m
    diameter_of_wheel = 6.5/100. #m
    intergration_time = 350./1000. #sec, TBD
    w = np.abs(steering_angle) * distance_between_opposite_wheels / diameter_of_wheel / intergration_time
    power_ratio_angle = np.abs(1. - w/300)
    power_ratio_distance = np.abs(1 - np.abs(relative_distance_from_center))

    total_power_ratio = np.sqrt(power_ratio_angle**2 + power_ratio_distance**2)/np.sqrt(2)

    # total_power_ratio = (power_ratio_distance + power_ratio_angle)/2


    return total_power_ratio




def auto_guide(frame, color="white"):

    img = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    steering_angle, relative_distance_from_center = steering_angle_calculation(img, color=color)
    # power_change = Power_Change(steering_angle, relative_distance_from_center)

    return steering_angle, relative_distance_from_center

