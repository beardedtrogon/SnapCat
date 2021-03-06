﻿"""
███████╗███╗   ██╗ █████╗ ██████╗  ██████╗ █████╗ ████████╗
██╔════╝████╗  ██║██╔══██╗██╔══██╗██╔════╝██╔══██╗╚══██╔══╝
███████╗██╔██╗ ██║███████║██████╔╝██║     ███████║   ██║   
╚════██║██║╚██╗██║██╔══██║██╔═══╝ ██║     ██╔══██║   ██║   
███████║██║ ╚████║██║  ██║██║     ╚██████╗██║  ██║   ██║   
╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝      ╚═════╝╚═╝  ╚═╝   ╚═╝                  
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import argparse
import cv2
import numpy as np
import shutil
from win32api import GetSystemMetrics
import json_database
import tools
import random
import signal
import sys

LEFT_KEY = 2424832
RIGHT_KEY = 2555904
DOWN_KEY = 2621440

ESCAPE_KEY = 27
BACKSPACE_KEY = 8
RED = ( 200, 0, 0 )
GREEN = ( 0, 150, 0 )
YELLOW = ( 150, 150, 0 )

WHITE = ( 255, 255, 255 )
INVALID_STRING = "not_cat"
VALID_STRING = "cat"
UNSURE_STRING = "unsure"
NONE_STRING = "none"
POLLING_DURATION_MS = 100
MAX_POLLING_TIMEOUT_MS = (60 * 2 * 1000) #2 mins

IMAGE_TEXT = "Does Image Contain Cat?"
IMAGE_PATH = os.path.join( os.path.dirname( os.path.realpath(__file__) ), "images" )
USAGE_IMG = os.path.join( IMAGE_PATH, "usage.jpg" )


def get_max_window_size():

  width = GetSystemMetrics(0)
  height = GetSystemMetrics(1)

  max_size = min(width, height) * 0.75

  return int(max_size)

def resize_image( image ):
  max_window_size = get_max_window_size()
  window_size = max( image.shape[0], image.shape[1] )

  ratio = max_window_size / window_size

  dimensions = ( int( image.shape[1] * ratio ) , int( image.shape[0] * ratio) )

  # resize image
  image = cv2.resize(image, dimensions)

  return image

ARROWS_IMG = os.path.join( IMAGE_PATH, "cat-notcat.jpg" )
ARROWS_IMG = cv2.imread( ARROWS_IMG, cv2.IMREAD_COLOR)
ARROWS_IMG = resize_image(ARROWS_IMG)

ARROWS_IMG_GREYED = os.path.join( IMAGE_PATH, "cat-notcat-unavailable.jpg" )
ARROWS_IMG_GREYED = cv2.imread( ARROWS_IMG_GREYED, cv2.IMREAD_COLOR)
ARROWS_IMG_GREYED = resize_image(ARROWS_IMG_GREYED)

LOGO_IMG = os.path.join( IMAGE_PATH, "logo.jpg" )
LOGO_IMG = cv2.imread( LOGO_IMG, cv2.IMREAD_COLOR)
LOGO_IMG = resize_image(LOGO_IMG)

def create_blank( image, rgb_color=(0, 0, 0)):

  height = image.shape[0]
  width = image.shape[1]

  """Create new image(numpy array) filled with certain color in RGB"""
  # Create black blank image
  image = np.zeros((height, width, 3), np.uint8)

  # Since OpenCV uses BGR, convert the color first
  color = tuple(reversed(rgb_color))
  # Fill image with color
  image[:] = color

  return image

def display_image_wait_key( image, delay_ms=0 ):

  cv2.imshow(IMAGE_TEXT, image)
  return cv2.waitKeyEx( delay_ms )


def display_image_no_key( image, delay_ms=0 ):
  
  image = concatenate_images( LOGO_IMG, image )
  image = concatenate_images( image, ARROWS_IMG_GREYED )

  cv2.imshow(IMAGE_TEXT, image)
  return cv2.waitKeyEx( delay_ms )

# todo combine these two functions
def concatenate_images( image1, image2 ):
  
  ratio = image2.shape[1] / image1.shape[1]
  dimensions = ( image1.shape[1], int(image2.shape[0] / ratio) )
  
  # resize image
  resized = cv2.resize(image2, dimensions)
  return np.concatenate( ( image1, resized ), axis=0)


def move_images( image_dir, image_labels, outdir ):
  
  valid_dir = os.path.join( outdir, VALID_STRING )
  invalid_dir = os.path.join( outdir, INVALID_STRING )

  # iterate over all the labeled images and put them within a foler
  for file, label in image_labels:

    file_dir = file.split(image_dir)[1] # split path to find any sub directories
    if file_dir[0] == '\\':
      file_dir = file_dir[1:] # get rid of the first slash on the filename

    if label == VALID_STRING:
      new_file = os.path.join( valid_dir, file_dir )

    if label == INVALID_STRING:
      new_file = os.path.join( invalid_dir, file_dir )

    # make sure the new sub directory exists
    new_file_dir = os.path.dirname(new_file)
    if not os.path.isdir( new_file_dir ):
      os.makedirs( new_file_dir )

    #print(file, new_file)
    os.rename(file, new_file )


def move_directories( image_dir, directory_labels, outdir ):
  
  valid_dir = os.path.join( outdir, VALID_STRING )
  invalid_dir = os.path.join( outdir, INVALID_STRING )

  # iterate over all the labeled images and put them within a foler
  for directory, label in directory_labels:

    file_dir = directory.split(image_dir)[1] # split path to find any sub directories
    if file_dir[0] == '\\':
      file_dir = file_dir[1:] # get rid of the first slash on the filename

    if label == VALID_STRING:
      new_dir = os.path.join( valid_dir, file_dir )

    if label == INVALID_STRING:
      new_dir = os.path.join( invalid_dir, file_dir )

    # make sure the new sub directory exists
    new_file_dir = os.path.dirname(new_dir)
    if not os.path.isdir( new_file_dir ):
      os.makedirs( new_file_dir )

    #print(directory, new_dir)
    shutil.move(directory, new_dir )



def disp_image_get_input( image, snapcat_json ):

  # iterate over all files and add label
  timeout = 0

  while True:

    if timeout > MAX_POLLING_TIMEOUT_MS:
      key = 1234
      timeout = 0
    else:
      # display image to be labeled
      key = display_image_wait_key( image, POLLING_DURATION_MS )

    # wait for user input
    if key == LEFT_KEY:
      update = cv2.add(image, create_blank( image, RED) )
      display_image_wait_key( update, POLLING_DURATION_MS)
      return key

    elif key == RIGHT_KEY:
      update = cv2.add( image, create_blank( image, GREEN ) )
      display_image_wait_key( update, POLLING_DURATION_MS )
      return key

    elif key == DOWN_KEY:
      update = cv2.add( image, create_blank( image, YELLOW ) )
      display_image_wait_key( update, POLLING_DURATION_MS )
      return key

    elif key == ESCAPE_KEY:
      return key

    elif key == BACKSPACE_KEY:
      return key

    elif key != -1:
      alpha = 0.3

      # image to review as backgorund and usage as foreground
      prev_img = image

      # resize images
      # resize the second image to be the same as the first no matter the original size
      img1 = resize_image(image)
      img2 = cv2.resize(cv2.imread(USAGE_IMG), ( img1.shape[1] , img1.shape[0] ))

      image = cv2.addWeighted(img1,alpha,img2,1-alpha,0)

      snapcat_json.save()

      display_image_wait_key( image, 0)
      image = prev_img

      key = -1

    else:
      timeout += POLLING_DURATION_MS

def display_directory_get_input( files ):
  timeout = 0

  first_pass = True

  images = []
  for file in files:
    image = cv2.imread( file, cv2.IMREAD_COLOR)
    image = concatenate_images( LOGO_IMG, image )
    image = concatenate_images( image, ARROWS_IMG )

    images.append( resize_image(image) )

  images_greyed = []
  for file in files:
    image = cv2.imread( file, cv2.IMREAD_COLOR)
    image = concatenate_images( LOGO_IMG, image )
    image = concatenate_images( image, ARROWS_IMG_GREYED )

    images_greyed.append( resize_image(image) )

  import time
  mytime = time.time()
  # iterate over all files and add label
  while True:

    for i in range(len(images)):

      if timeout > MAX_POLLING_TIMEOUT_MS:
        key = 1234
        timeout = 0
      else:

        # TODO: write a script to reduce the amount of images in a burst to less than 20 images
        if first_pass:
          mytime = time.time()
          image = images_greyed[i]
          display_image_wait_key( image, POLLING_DURATION_MS )
          key = -1
        else:
          image = images[i]
          key = display_image_wait_key( image, POLLING_DURATION_MS )
      
      # wait for user input
      if key == LEFT_KEY:
        update = cv2.add(image, create_blank(image, RED))
        display_image_wait_key( update, POLLING_DURATION_MS)
        return key

      elif key == RIGHT_KEY:
        update = cv2.add(image, create_blank(image, GREEN))
        display_image_wait_key( update, POLLING_DURATION_MS)
        return key

      elif key == DOWN_KEY:
        update = cv2.add( image, create_blank( image, YELLOW ) )
        display_image_wait_key( update, POLLING_DURATION_MS )
        return key

      elif key == ESCAPE_KEY:
        return key

      elif key == BACKSPACE_KEY:
        return key

      elif key != -1:

        alpha = 0.3

        # image to review as backgorund and usage as foreground
        prev_img = image

        # resize images
        # resize the second image to be the same as the first no matter the original size
        img1 = resize_image(image)
        img2 = cv2.resize(cv2.imread(USAGE_IMG), ( img1.shape[1] , img1.shape[0] ))

        image = cv2.addWeighted(img1,alpha,img2,1-alpha,0)

        snapcat_json.save()

        display_image_wait_key( image, 0)
        image = prev_img

        key = -1

        first_pass = True
        i = 0
      
      elif key == -1:
        timeout += POLLING_DURATION_MS

    first_pass = False


def update_aoi_label ( snapcat_json, image_name, aoi_user_labels ):
  # TODO - save a count of the times the image has been labeled this
  snapcat_json.update( image_name, "aoi_user_label", aoi_user_labels ) # TODO - user_label will be associated with area of interest
  snapcat_json.save()

def update_label ( snapcat_json, image_name, user_label ):
  # TODO - save a count of the times the image has been labeled this
  
  snapcat_json.update( image_name, "user_label", user_label)
  #snapcat_json.save()

def user_label_images_single( snapcat_json ):  
  ######################### sort individual files #########################

  done = False
  index = 0

  image_list = []
  for image in snapcat_json.json_data:
    try:
      tmp = snapcat_json.json_data[image]["aoi_user_labels"]
      continue
    except:
      try:
        tmp = snapcat_json.json_data[image]["user_label"]
        continue
      except:
        image_list.append(image)

  # shuffle the images so the user isn't tempted to use previously viewed images to determine if the image contains a cat
  random.shuffle(image_list)

  while not done:

    # load the image and areas of interest
    image = image_list[index]
    image_path = snapcat_json.json_data[image]["path"]
    try:
      areas_of_interest = snapcat_json.json_data[image]["areas_of_interest"]
    except:
      areas_of_interest = []

    aoi_user_labels = []

    if len(areas_of_interest) == 0:
      img = cv2.imread(image_path, cv2.IMREAD_COLOR)

      if type(img) == type(None):
        index += 1
        continue

      y,x,_ = img.shape

      #print("image:", image )

      x1,x2,y1,y2 = tools.optimal_square(400,x-400,400,y-400,img)

      subimg = img[y1:y2,x1:x2,:]
      resized_image = cv2.resize(subimg, (224, 224))

      key = disp_image_get_input( resized_image, snapcat_json )

      if key == LEFT_KEY:
        # TODO - make sure the label is associated with the area of interest instead of the label
        update_label( snapcat_json, image, INVALID_STRING )
        index = index + 1
        continue

      elif key == RIGHT_KEY:
        # TODO - make sure the label is associated with the area of interest instead of the label
        update_label( snapcat_json, image, VALID_STRING )
        index = index + 1
        continue

      elif key == DOWN_KEY:
        # TODO - make sure the label is associated with the area of interest instead of the label
        aoi_user_labels.append(UNSURE_STRING)
        update_label( snapcat_json, image, UNSURE_STRING )
        index = index + 1
        continue

      elif key == BACKSPACE_KEY:
        # ensure we don't go negative with the index
        if ( index > 0 ):
          index = index - 1      
        update_label( snapcat_json, image, NONE_STRING )
        continue

      elif key == ESCAPE_KEY:
        cv2.destroyAllWindows()
        done = True
        continue

    for area_of_interest in areas_of_interest:
        
      # todo - skip if already contains a label?

      # populate x, y coordinates of the areas of interest
      x1 = area_of_interest[0]
      x2 = area_of_interest[1]
      y1 = area_of_interest[2]
      y2 = area_of_interest[3]

      # crop the image to the area of interest
      img = cv2.imread(image_path, cv2.IMREAD_COLOR)
      #print("image_path, :", image_path )
      #print("img:", img )
      img = img[y1:y2 , x1:x2, :]

      # todo - determine the size we want - this will be the size fed into the classifier, so it may make sense to use that
      resized_image = cv2.resize(img, (224, 224))

      key = disp_image_get_input( resized_image, snapcat_json )
      
      if key == LEFT_KEY:
        # TODO - make sure the label is associated with the area of interest instead of the label
        aoi_user_labels.append(INVALID_STRING)
        #update_aoi_label( snapcat_json, image_name, INVALID_STRING, aoi_count )
        index = index + 1

      elif key == RIGHT_KEY:
        # TODO - make sure the label is associated with the area of interest instead of the label
        aoi_user_labels.append(VALID_STRING)
        #update_aoi_label( snapcat_json, image_name, VALID_STRING, aoi_count )
        index = index + 1

      elif key == DOWN_KEY:
        # TODO - make sure the label is associated with the area of interest instead of the label
        aoi_user_labels.append(UNSURE_STRING)
        #update_aoi_label( snapcat_json, image_name, UNSURE_STRING, aoi_count )
        index = index + 1

      elif key == BACKSPACE_KEY:
        # ensure we don't go negative with the index
        if ( index > 0 ):
          index = index - 1

        if len(aoi_user_labels) > 0:      
          aoi_user_labels.pop()

        update_label( snapcat_json, image, NONE_STRING )
      elif key == ESCAPE_KEY:
        cv2.destroyAllWindows()
        done = True

      update_aoi_label( snapcat_json, image, aoi_user_labels )
    
    if  index >= len(image_list):
      done = True

  snapcat_json.save()
  cv2.destroyAllWindows()


def update_user_burst_label( snapcat_json, burst, label ):
  for image_name in burst:
    snapcat_json.update( image_name, "user_burst_label", label )
     
  #snapcat_json.save()


def user_label_images_burst( snapcat_json ):
  ######################### sort image bursts #########################

  bursts = tools.get_bursts( snapcat_json )

  # Skip bursts that definitely contain a cat
  # only review bursts that have an unsure label
  unsure_bursts = []

  random.shuffle(bursts)

  for burst in bursts:

    image_labeled = False
    
    num_burst_images = len(burst)
    for image_name in burst:

      #TODO - classifier_label will be associated with an area of interest
      if image_name in snapcat_json.json_data and "classifier_label" in snapcat_json.json_data[image_name] and snapcat_json.json_data[image_name]["classifier_label"] == "cat":
        image_labeled = True
        break

      if image_name in snapcat_json.json_data and "user_burst_label" in snapcat_json.json_data[image_name] and snapcat_json.json_data[image_name]["user_burst_label"] != None:
        image_labeled = True
        break

      if image_name in snapcat_json.json_data and "areas_of_interest" in snapcat_json.json_data[image_name] and "aoi_user_labels" in snapcat_json.json_data[image_name]:
        num_aoi = len(snapcat_json.json_data[image_name]["areas_of_interest"])
        num_aois_labeled = len(snapcat_json.json_data[image_name]["aoi_user_labels"])

        if num_aoi == num_aois_labeled:
          break

    if not image_labeled:
      unsure_bursts.append( burst )

  # iterate over all of the bursts and get a label
  if len(unsure_bursts) == 0:
    if len(bursts) == 0:
      print("ERROR: there were no images to classify")
    else:
      print("No images remain to be classified - done")
    return

  done = False
  index = 0

  while not done:
    image_list = []

    for image_name in unsure_bursts[index]:
      image_path = snapcat_json.json_data[image_name]["path"]
      if os.path.isfile(image_path):
        image_list.append(image_path)
      else:
        print("ERROR: image does not exist:", image_path)

      
    #print( image_list )

    directories_to_ignore = [ "Cabritos_Part2\\camara 08",
                              "Mona\\27", 
                              "Mona\\5A",
                              "trampa\\piedra a 1" ]

    skip = False
    for image in image_list:  
      for ignore_string in directories_to_ignore:
        if ignore_string in image:
          print("ignoring image:", image)
          skip = True
        else:
          print("image:", image)
      
    if skip:
      index = index + 1
      continue
      
    key = display_directory_get_input( image_list )
    
    if key == LEFT_KEY:
      update_user_burst_label( snapcat_json, unsure_bursts[index], INVALID_STRING)
      index = index + 1

    elif key == RIGHT_KEY:
      update_user_burst_label( snapcat_json, unsure_bursts[index], VALID_STRING)
      index = index + 1

    elif key == DOWN_KEY:
      update_user_burst_label( snapcat_json, unsure_bursts[index], UNSURE_STRING)
      index = index + 1

    elif key == BACKSPACE_KEY:
      # ensure we don't go negative with the index
      if ( index > 0 ):
        index = index - 1

      update_user_burst_label( snapcat_json, unsure_bursts[index], NONE_STRING )

    elif key == ESCAPE_KEY:
      cv2.destroyAllWindows()
      done = True
    
    if index >= len(unsure_bursts):
      done = True

  cv2.destroyAllWindows()
  snapcat_json.save()
  

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--json_dir", help="path to the json database for images" )
  parser.add_argument("--burst", help="display all images from burst or not", default="false" )

  args = parser.parse_args()
  
  snapcat_json = json_database.JSONDatabase( args.json_dir )

  if args.burst.lower() == "true":
    #print("burst")
    user_label_images_burst( snapcat_json )
  else:
    user_label_images_single( snapcat_json )
