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

def purge_database( snapcat_json, key_to_remove ):
    for image in snapcat_json.json_data:
        snapcat_json.remove( image , key_to_remove )
    snapcat_json.save()

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--json_dir", help="path to the json database for images" )
  parser.add_argument("--key_to_remove", help="key in the database to remove" )
  args = parser.parse_args()

  snapcat_json = json_database.JSONDatabase( args.json_dir )
  purge_database( snapcat_json, args.key_to_remove )
