"""
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

import numpy as np
import tensorflow as tf

import settings
import tools
import json_database
import cv2
from skimage import img_as_ubyte

import tempfile #todo remove this once we figure out how to pass the image in directly

def label_images( snapcat_json ):

  model_file = settings.graph['graph']
  label_file = settings.graph['labels']
  input_height = settings.graph['input_height']
  input_width = settings.graph['input_width']
  input_mean = settings.graph['input_mean']
  input_std = settings.graph['input_std']
  input_layer = settings.graph['input_layer']
  output_layer = settings.graph['output_layer']

  graph = tools.load_graph(model_file)
  labels = tools.load_labels(label_file)

  # Create Full path
  # todo, should this be outside the loop, one TF session and then parse all the images?
  with tf.Session(graph=graph) as sess:

    for image in snapcat_json.json_data:

      file = snapcat_json.json_data[image]["path"]

      if not os.path.isfile(file):
        print("***************ERROR - File doesn't exist:", file)
        continue
      
      # resize area of interest for classification
      #TODO - modify for multiple areas of interest
      area_of_interest = snapcat_json.json_data[image]["area_of_interest"]
      x1 = area_of_interest[0]
      x2 = area_of_interest[1]
      y1 = area_of_interest[2]
      y2 = area_of_interest[3]

      img = cv2.imread(file)
      img = img[y1:y2 , x1:x2, :]

      resized_image = cv2.resize(img, (input_width, input_height))
      t = (np.float32(resized_image) - input_mean) / input_std

      input_name = "import/" + input_layer
      output_name = "import/" + output_layer
      input_operation = graph.get_operation_by_name(input_name)
      output_operation = graph.get_operation_by_name(output_name)

      # todo, suspect this is what's printing a lot of messages. Attempt to consolidate calls to this function
      results = sess.run(output_operation.outputs[0], {
        input_operation.outputs[0]: [t]
      })

      results = np.squeeze(results)

      # get classification
      top_k = results.argsort()[-5:][::-1]
      for i in top_k:
        
        # if confidence level is below certain value, put in "unsure" folder
        print("%s: %f" % (labels[i], results[i]))
        if results[i] >= settings.sort_image['cat_confidence_threshold'] and labels[i] == 'cats':
          print("cat")
          snapcat_json.update( image , "classifier_label", "cat" ) #TODO - classifier_label will be associated with an area of interest
        elif results[i] >= settings.sort_image['not_cat_confidence_threshold'] and labels[i] == 'not cats':
          print("not cat")
          snapcat_json.update( image , "classifier_label", "not_cat" ) #TODO - classifier_label will be associated with an area of interest
        else:
          print("unsure")
          snapcat_json.update( image , "classifier_label", "unsure" ) #TODO - classifier_label will be associated with an area of interest
          
        break

    snapcat_json.save()

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--json_dir", help="path to the json database for images" )
  args = parser.parse_args()

  snapcat_json = json_database.JSONDatabase( args.json_dir )
  label_images( snapcat_json )
