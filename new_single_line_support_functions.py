#!/usr/bin/env python
# coding: Latin-1

import cv2
import numpy as np 
import time


def mask_color(frame, color):
    # Light Environment
    # white = [[70, 10, 150], [255, 255, 255]]
    # orange = [[1, 10, 60], [15, 200, 220]]
    # frame = cv2.medianBlur(frame,11)
    
    # Dark Environment
    # white = [[50, 0, 160], [180, 100, 255]]
    # orange = [[0, 0, 50], [15, 255, 255]]

    # HLS
    white = [[0, 150, 0], [255, 255, 255]]
    orange = [[0, 0, 50], [15, 255, 255]]


    if color=='white':

        lower = np.array(white[0])
        upper = np.array(white[1])

    elif color=='orange':
        lower = np.array(orange[0])
        upper = np.array(orange[1])
        

    mask = cv2.inRange(frame, lower ,upper)
    output = cv2.bitwise_and(frame, frame, mask = mask)

    # time_1 = time.time()
    # # if u want the above output change the return
    # output = cv2.adaptiveThreshold(frame[:,:,2],255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,149,-12)
    # time_2 = time.time()
    # print(time_2 - time_1)

    return output, mask


def steering_angle_calculation(frame, color, value_threshold=80):
    
    masked_image, _ = mask_color(frame, color=color)
    print np.max(masked_image)
    sums = np.sum(masked_image, axis=2)
    height, width = sums.shape
    flag_end_of_line_on_x = False
    try:
        (y,x)=np.where(sums > value_threshold)
        
        
        # --------------------------------------------------
        # New condition for when the line has a slope > 45 deg
        # --------------------------------------------------
        length_of_top_row = len(x[np.where(y==np.min(y))])
        
        if length_of_top_row < 20:
            (x,y)=np.where(sums > value_threshold)
            flag_end_of_line_on_x = True

            # x_max_median = np.median(x[np.where(y==np.min(y))])
            # x_min_median = np.median(x[np.where(y==np.max(y)-30)])
            # y_max = np.max(y) - 30
            # y_min = np.min(y)
            # y_middle_line = width/2
            # x_middle_line = height/2
            # x_middle_calc_line = (y_min + y_max)/2
            # y_middle_calc_line = (x_min_median + x_max_median)/2


            x_min_median = np.median(x[np.where(y==np.min(y))])
            x_max_median = np.median(x[np.where(y==np.max(y))])

            y_max = np.max(y) - 30
            y_min = np.min(y)

        
            y_middle_calc_line = (y_min + y_max)/2
            x_middle_calc_line = (x_min_median + x_max_median)/2

        
            y_middle_line = height/2
            x_middle_line = width/2



        # --------------------------------------------------
        # --------------------------------------------------
        else:
            x_min_median = np.median(x[np.where(y==np.min(y))])
            x_max_median = np.median(x[np.where(y==np.max(y)-30)])

            y_max = np.max(y) - 30
            y_min = np.min(y)

        
            y_middle_calc_line = (y_min + y_max)/2
            x_middle_calc_line = (x_min_median + x_max_median)/2

        
            y_middle_line = height/2
            x_middle_line = width/2
            
        



        if x_middle_calc_line - x_middle_line < 0:
            distance_from_center = -np.sqrt((x_middle_calc_line - x_middle_line)**2 + (y_middle_calc_line - y_middle_line)**2)
        else:
            distance_from_center = np.sqrt((x_middle_calc_line - x_middle_line)**2 + (y_middle_calc_line - y_middle_line)**2)
        

        relative_distance_from_center = distance_from_center / (width/2)
        # print("relative distance from center", relative_distance_from_center)
            

        if x_min_median != x_max_median:
            # --------------------------------------------------
            # New condition for when the line has a slope > 45 deg
            # --------------------------------------------------
            if flag_end_of_line_on_x:
                steering_angle = np.rad2deg(-np.arctan((x_min_median - x_max_median)/(y_min - y_max)))
            # --------------------------------------------------
            # --------------------------------------------------
            else:
                steering_angle = np.rad2deg(-np.arctan((y_min - y_max)/(x_min_median - x_max_median)))
            
        elif x_min_median == x_max_median:
            steering_angle = 0

        
        if steering_angle < 0:
            corr_steering_angle = -(steering_angle + 90)
        elif steering_angle > 0:
            corr_steering_angle = 90 - steering_angle
        else:
            corr_steering_angle = 0
        
        if np.abs(corr_steering_angle) < 8:
            corr_steering_angle = 0
        else:
            pass

    except:
        print("no line detected")
        corr_steering_angle = 0
        relative_distance_from_center = 0
        x_min_median = width/2
        x_max_median = width/2
        y_min = 0
        y_max = height
        steering_angle = 0
    
    # print(corr_steering_angle)
    
    return corr_steering_angle, relative_distance_from_center, x_min_median, y_min, x_max_median, y_max, flag_end_of_line_on_x






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

    img = cv2.cvtColor(frame, cv2.COLOR_BGR2HLS)
    steering_angle, relative_distance_from_center, _, _, _, _, _ = steering_angle_calculation(img, color=color)
    # power_change = Power_Change(steering_angle, relative_distance_from_center)

    return steering_angle, relative_distance_from_center

