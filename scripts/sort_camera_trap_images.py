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

import argparse
import os
import burst
import segmentation
from label_images import label_images
import user_label_image
import generate_report
import shutil
import datetime
import json_database

def sort_camera_trap_images( unsorted_dir ):

  json_name = os.path.basename(os.path.dirname(unsorted_dir)) + ".json"
  snapcat_database_dir = os.path.join( unsorted_dir, json_name )
  snapcat_json = json_database.JSONDatabase( snapcat_database_dir )
  
  burst.create_bursts( snapcat_json, unsorted_dir )
  #segmentation.segment_images( snapcat_json )
  
  #label_images( snapcat_json ) 

  # TODO make sure this is working well to deliver to Island conservation.
  # make sure the label is saved in the dataset
  user_label_image.user_label_images_burst( snapcat_json )
  
  generate_report.generate_report( snapcat_json, unsorted_dir )


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--unsorted_dir", help="directory containing camera images")
  
  args = parser.parse_args()
  
  sort_camera_trap_images( args.unsorted_dir)

