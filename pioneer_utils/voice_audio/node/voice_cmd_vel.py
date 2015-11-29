#!/usr/bin/env python

"""
voice_cmd_vel.py is a simple demo of speech recognition.
  You can control a mobile base using commands found
  in the corpus file.
"""

import roslib; roslib.load_manifest('pocketsphinx')
import roslib
import rospy
import math
import subprocess
import os, signal
import time
import psutil

from std_msgs.msg import String

from sound_play.libsoundplay import SoundClient

import actionlib
import tf
from actionlib_msgs.msg import *
from geometry_msgs.msg import Pose, PoseWithCovarianceStamped, Point, Quaternion, Twist
from nav_msgs.msg import Odometry
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from random import sample
from math import pow, sqrt

def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.get_children(recursive=True):
        proc.terminate()
    process.terminate()

def trunc(f, n):
    # Truncates/pads a float f to n decimal places without rounding
    slen = len('%.*f' % (n, f))
    return float(str(f)[:slen])

class voice_cmd_vel:

    def __init__(self):
        rospy.loginfo("STAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAARTTTTTTTTTTTTTTTTTTTTT")
        rospy.on_shutdown(self.cleanup)
        self.speed = 0.1
        self.buildmap = False
        self.follower = False
        self.navigation = False
        self.msg = Twist()
        
        # How long in seconds should the robot pause at each location?
        self.rest_time = rospy.get_param("~rest_time", 10)
        
        # .txt file with name and x, y coordinates for location
        self.map_locations = rospy.get_param("~map_locations")
        
        # odometry topic name
        self.odometry_topic = rospy.get_param("~odometry_topic", "odom")
        
        # cmd_vel topic name
        self.cmd_vel_topic = rospy.get_param("~cmd_vel_topic", "cmd_vel")
        rospy.loginfo("CMD_VEL TOPIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIICCCCCCCCCCCCCCCCCC")
                       
        self.locations = dict()
        rospy.loginfo("BEFOOOOOREEEEEEEEEEEE READ FILEEEEEEEEEEEEEEEEEEEEEEEEE")
        fh=open(self.map_locations)
        for line in fh:
            name = line.rstrip().split(":")
            rospy.loginfo("NAMEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE")
            temp = str(line.rstrip().rsplit(":", 1)[1])
            coordinates = temp.split()
            rospy.loginfo("COORDINAAAAAAAAAAAAAAAAAAAAAAAATEEEEEEEEEEEEEESSSSSSSSSSSS")
            locations[str(name[0])] = Pose(Point(float(coordinates[0]), float(coordinates[1]), 0.000), Quaternion(*tf.transformations.quaternion_from_euler(0, 0, 0)))
            rospy.loginfo("LOCATIOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOONNSSSSSSSSSSSSSSSSSSSSSS")
        rospy.loginfo("REAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD FIIIIIIIIILEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE")

        # Create the sound client object
        self.soundhandle = SoundClient()
       
        rospy.sleep(1)
        self.soundhandle.stopAll()
        
         # Subscribe to the move_base action server
        self.move_base = actionlib.SimpleActionClient("move_base", MoveBaseAction)
        
        rospy.loginfo("Waiting for move_base action server...")
        
        # Wait 60 seconds for the action server to become available
        self.move_base.wait_for_server(rospy.Duration(60))
        
        rospy.loginfo("Connected to move base server")
       
        # Announce that we are ready for input
        rospy.sleep(1)
        self.soundhandle.say('Hi, my name is Petrois')
        rospy.sleep(2)
        self.soundhandle.say("Say one of the navigation commands")

        # publish to cmd_vel, subscribe to speech output
        self.pub = rospy.Publisher(self.cmd_vel_topic, Twist, queue_size=2)
        rospy.Subscriber('recognizer/output', String, self.speechCb)

        r = rospy.Rate(10.0)
        while not rospy.is_shutdown():
            self.pub.publish(self.msg)
            r.sleep()
        
    def speechCb(self, msg):
        rospy.loginfo(msg.data)

        if msg.data.find("fast") > -1:
            if self.speed != 0.3:
                self.soundhandle.say('Speeding up')
                if self.msg.linear.x > 0:
                    self.msg.linear.x = 0.3
                elif self.msg.linear.x < 0:
                    self.msg.linear.x = -0.3
                if self.msg.angular.z >0:
                    self.msg.angular.z = 0.3
                elif self.msg.angular.z < 0:
                    self.msg.angular.z = -0.3
                self.speed = 0.3
            else:
                self.soundhandle.say('Already at full speed')

        if msg.data.find("half") > -1:
            if self.speed != 0.2:
                self.soundhandle.say('Going at half speed')
                if self.msg.linear.x > 0:
                    self.msg.linear.x = 0.2
                elif self.msg.linear.x < 0:
                    self.msg.linear.x = -0.2
                if self.msg.angular.z >0:
                    self.msg.angular.z = 0.2
                elif self.msg.angular.z < 0:
                    self.msg.angular.z = -0.2
                self.speed = 0.2
            else:
                self.soundhandle.say('Already at half speed')

        if msg.data.find("slow") > -1:
            if self.speed != 0.1:
                self.soundhandle.say('Slowing down')
                if self.msg.linear.x > 0:
                    self.msg.linear.x = 0.1
                elif self.msg.linear.x < 0:
                    self.msg.linear.x = -0.1
                if self.msg.angular.z >0:
                    self.msg.angular.z = 0.1
                elif self.msg.angular.z < 0:
                    self.msg.angular.z = -0.1
                self.speed = 0.1
            else:
                self.soundhandle.say('Already at slow speed')

        if msg.data.find("forward") > -1:
            self.soundhandle.play(1)    
            self.msg.linear.x = self.speed
            self.msg.angular.z = 0
        elif msg.data.find("left") > -1:
            self.soundhandle.play(1)
            if self.msg.linear.x != 0:
                if self.msg.angular.z < self.speed:
                    self.msg.angular.z += 0.05
            else:        
                self.msg.angular.z = self.speed*2
        elif msg.data.find("right") > -1:
            self.soundhandle.play(1)    
            if self.msg.linear.x != 0:
                if self.msg.angular.z > -self.speed:
                    self.msg.angular.z -= 0.05
            else:        
                self.msg.angular.z = -self.speed*2
        elif msg.data.find("back") > -1:
            self.soundhandle.play(1)
            self.msg.linear.x = -self.speed
            self.msg.angular.z = 0
        elif msg.data.find("stop") > -1 or msg.data.find("halt") > -1:
            self.soundhandle.play(1)
            self.msg = Twist()

################################# follower commands
        
        if msg.data.find("follow me") > -1:
            if self.follower == False:
                self.msg = Twist()
                self.proc1 = subprocess.Popen(['roslaunch', 'pioneer_utils', 'simple-follower.launch'])
                self.soundhandle.say('Okay. Show me the way')
                self.follower = True
            else:
                self.soundhandle.say('Already in follower mode')
		
        elif msg.data.find("stop follower") > -1:
            if self.follower == True:
                self.msg = Twist()
                print 'proc1 = ', self.proc1.pid
                self.proc1.terminate()
                kill(self.proc1.pid)
                self.proc1.kill()
                self.follower = False
                self.soundhandle.say('Follower mode disabled')
            else:
                self.soundhandle.say('Hey, I wasnt following you')

################################ map commands

        if msg.data.find("build map") > -1:
            if self.buildmap == False:
                self.soundhandle.say('Building map with slam gmapping')
                rospy.sleep(2)
                self.soundhandle.say('Visualizing map')
                self.msg = Twist()
                self.proc2 = subprocess.Popen(['roslaunch', 'p2os_launch', 'gmapping.launch'])
                self.proc3 = subprocess.Popen(['roslaunch', 'pioneer_utils', 'rviz-gmapping.launch'])
                self.buildmap = True
            else:
                self.soundhandle.say('Already building a map')


        elif msg.data.find("save map") > -1:
            if self.buildmap == True:
                self.msg = Twist()
                self.proc4 = subprocess.Popen(['rosrun', 'map_server', 'map_saver', '-f', 'new_map'])
                rospy.sleep(6)
                print 'map saved at ~/.ros directory as new_map.pgm new_map.yaml'
                self.soundhandle.say('Map saved successfully')
            else:
                self.soundhandle.say('I am not building any map so there is no map to save')
		
        elif msg.data.find("stop map") > -1:
            if self.buildmap == True:
               self.msg = Twist() 
               print 'proc2 = ', self.proc2.pid
               self.proc2.terminate()
               kill(self.proc2.pid)
               self.proc2.kill()
               print 'proc3 = ', self.proc3.pid
               self.proc3.terminate()
               kill(self.proc3.pid)
               self.proc3.kill()
               print 'proc4 = ', self.proc4.pid
               self.proc4.terminate()
               kill(self.proc4.pid)
               self.proc4.kill()
               self.buildmap = False
               self.soundhandle.say('Building map stopped')
            else:
               self.soundhandle.say('I am not building any map')

################################ navigation commands

        if msg.data.find("navigate") > -1:
            if self.navigation == False:
                self.soundhandle.say('Starting navigation stack')
                rospy.sleep(2)
                self.soundhandle.say('Visualizing costmaps')
                self.msg = Twist()
                self.proc5 = subprocess.Popen(['roslaunch', 'pioneer_utils', 'navigation_p3at.launch'])
                self.proc6 = subprocess.Popen(['roslaunch', 'pioneer_utils', 'rviz-navigation.launch'])
                self.navigation = True
            else:
                self.soundhandle.say('Already in navigation mode')

        elif msg.data.find("stop navigation") > -1:
            if self.navigation == True:
                self.msg = Twist()
                print 'proc5 = ', self.proc5.pid
                self.proc5.terminate()
                kill(self.proc5.pid)
                self.proc5.kill()
                print 'proc6 = ', self.proc6.pid
                self.proc6.terminate()
                kill(self.proc6.pid)
                self.proc6.kill()
                self.navigation = False
                self.soundhandle.say('Navigation stopped')
            else:
                self.soundhandle.say('I am not in navigation mode')
                
        #elif msg.data.find("navigate to") > -1:
         #   if msg.data.split()[2] in location.keys():
          #      self.send_goal(msg.data.split()[2])

        self.pub.publish(self.msg)
        
    def send_goal(self, location_name):
        location = self.locations.get(location_name)
        # Set up goal location
        #self.goal = MoveBaseGoal()
        #self.goal.target_pose.pose = location
        #self.goal.target_pose.header.frame_id = 'map'
        #self.goal.target_pose.header.stamp = rospy.Time.now()
        #rospy.loginfo(self.goal)
            
        # Let the user know where the robot is going next
        #rospy.loginfo("Going to: " + str(location_name))
            
        # Start the robot toward the next location
        #self.move_base.send_goal(self.goal)
            
        # Allow 5 minutes to get there
        #finished_within_time = self.move_base.wait_for_result(rospy.Duration(300)) 
            
        # Check for success or failure
        #if not finished_within_time:
         #   self.move_base.cancel_goal()
          #  rospy.loginfo("Timed out achieving goal")
        #else:
         #   state = self.move_base.get_state()
          #  if state == GoalStatus.SUCCEEDED:
           #     rospy.loginfo("Goal succeeded!")
            #else:
             #   rospy.loginfo("Goal failed")

    def cleanup(self):
        # stop the robot!
        twist = Twist()
        #self.pub.publish(twist)

if __name__=="__main__":
    rospy.init_node('voice_cmd_vel')
    try:
        voice_cmd_vel()
    except:
        pass
