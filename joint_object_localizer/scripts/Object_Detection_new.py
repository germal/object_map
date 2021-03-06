#!/usr/bin/env python

# Libraries:
import rospy
import numpy as np
import time
from scipy.optimize import differential_evolution
from tf.transformations import quaternion_from_euler
from geometric_functions import Likelihood, quaternion_to_euler, New_Ce_array ,Ranges_to_xy_plane , Object_height_update

# Msgs:
from object_detector_ssd_tf_ros.msg import SSD_Outputs
from joint_object_localizer.msg import Object_Geometry , Optional_Theta , M_Suggested_List
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan

# test:
#from visualization_msgs.msg import Marker

# Callback functions:
def callback_laser(data):
    global scan_point
    scan_point = data

def Robot_callback(data):
    global Robot_Pose
    Robot_Pose = data

def SSD_callback(data):
    
    global SSD_info , got_new_ssd_msg
    SSD_info = data
    got_new_ssd_msg = True
def Odom_callback(data):
    global Robot_Odometry
    Robot_Odometry = data.pose.pose

rospy.init_node('Theta_values', anonymous=True)
# Publisher:

M_list_publisher = rospy.Publisher('/M_o',M_Suggested_List,queue_size = 10)
# Subscribers:
scan_point_sub = rospy.Subscriber('/scan' ,LaserScan , callback_laser )
rospy.wait_for_message('/scan',LaserScan)
Robot_sub = rospy.Subscriber('/slam_out_pose',PoseStamped,Robot_callback)
rospy.wait_for_message('/slam_out_pose',PoseStamped)
SSD_sub = rospy.Subscriber('/im_info',SSD_Outputs,SSD_callback,queue_size=1)
rospy.wait_for_message('/im_info',SSD_Outputs)
Robot_World_Location_sub = rospy.Subscriber('/odom',Odometry,Odom_callback)
rospy.wait_for_message('/odom',Odometry)

# YAMLs:
A_Round = np.array(rospy.get_param('/Array/round'))
A_Rectangle = np.array(rospy.get_param('/Array/rectangle'))
A_Elliptical = np.array(rospy.get_param('/Array/elliptical'))
Object_cls_list = np.array(rospy.get_param('/Array/object_list'))
correction_factor = rospy.get_param('/Cord_cor/Simulation/Correction')

global got_new_ssd_msg
#r = rospy.Rate(1)

while not rospy.is_shutdown():
    #Sr.sleep()

    data = SSD_info
    
    # If not a single object is seen by the camera:
    if data.outputs[0].cls == -1:
        M_S = M_Suggested_List()
        M_S.M_list = []
        M_list_publisher.publish(M_S)

    elif got_new_ssd_msg == True:
        
        got_new_ssd_msg = False
        M_S = M_Suggested_List()
        M_S.M_list = []
        
        # Calculating the maximum angle of the sensor:
        angle_jumps = scan_point.angle_increment
        phi_max = len(scan_point.ranges) * angle_jumps
        theta_camera_max = 1.4

        # The angle that needed to be added to the camera angle to get the angle for the sensor:
        correction_for_sensor = (phi_max + theta_camera_max) / 2
        size =  (len(scan_point.ranges) - 1)/2
        
        
        for ii in range (0,len(data.outputs)):

            Norm_factor = 0
            Theta_list = Optional_Theta()
            Theta_list.object_list = []
            

            # Getting the info from the camera:
            x_min_new = data.outputs[ii].x_min 
            x_max_new = data.outputs[ii].x_max
            y_min_new = data.outputs[ii].y_min
            y_max_new = data.outputs[ii].y_max
            SSD_probabilities = data.outputs[ii].probability_distribution

            cls_num = data.outputs[ii].cls
            
            
            # In case the object is not a one that can be stationed in the map:
            if cls_num not in Object_cls_list or y_min_new > 160 or y_max_new < 130:
                continue
            

            # Theta from camera:
            theta_min = x_min_new*(1.4/300)
            theta_max = x_max_new*(1.4/300)

            # Angle from the sensor:
            angle_max = int((correction_for_sensor - theta_min) / angle_jumps)
            angle_min = int((correction_for_sensor - theta_max) / angle_jumps)

                
            
            # Orientation of the robot from slam_out_pose:
            R_qx = Robot_Pose.pose.orientation.x
            R_qy = Robot_Pose.pose.orientation.y
            R_qz = Robot_Pose.pose.orientation.z
            R_qw = Robot_Pose.pose.orientation.w

            # Location of the robot from slam_out_pose: 
            x_R = Robot_Pose.pose.position.x
            y_R = Robot_Pose.pose.position.y
            '''

            # Orientation of the robot from the Odometry:
            R_qx = Robot_Odometry.orientation.x
            R_qy = Robot_Odometry.orientation.y
            R_qz = Robot_Odometry.orientation.z
            R_qw = Robot_Odometry.orientation.w

            # Location of the robot from Odometry: 
            x_R = Robot_Odometry.position.x
            y_R = Robot_Odometry.position.y
            '''
            # Euler orientation:
            [yaw, pitch, roll] = quaternion_to_euler(R_qx,R_qy,R_qz,R_qw)
            # Reading from the laser sensor:
            R = np.array(scan_point.ranges)
            # Transfer the (ranges,angle) poins into (x,y) points:
            laser_depth_observations = Ranges_to_xy_plane(R,angle_min,angle_max,
                                                            size,angle_jumps)
            # Not enough measurements or object is too far away:
            if len(laser_depth_observations) == 2:
                continue

            start_time = time.time()
            counter = 0
            # ------------------------Main algoritm start------------------------------------
            for jj in Object_cls_list:
                
                
                counter += 1
                # Round objects:
                if jj in A_Round:
                    
                    Theta_Object = Object_Geometry()
                    Theta_Object.height_factor = data.outputs[ii].height_factor
                    # Initializing the circle array:
                    circle = np.array((laser_depth_observations[angle_min:angle_max,:]))

                    bound_r = rospy.get_param('/object_list/o'+str(jj)+'/bound_r')

                    # Bounds for DE algoritm
                    bounds = [  [np.amin(circle[:,0])-0.1 , np.amin([np.amax(circle[:,0])+0.1 , 2.5])],
                                [np.amin(circle[:,1])-0.1 , np.amin([np.amax(circle[:,1])+0.1 , 2.5])],
                                bound_r]
                    
                    
                    C_class = Likelihood(class_number=jj,Z=circle,SSD_probability=SSD_probabilities)
                    # DE algoritm
                    circle_minimized_values = differential_evolution(C_class.probability_for_circle,bounds,
                                                                    maxiter = 50,  popsize=10, tol=0.00001)
                    
                    object_height = Object_height_update(Theta_Object.height_factor,
                                                        2*circle_minimized_values.x[2],
                                                        0,
                                                        0)
                    # Inserting the founded data:
                    v0 = New_Ce_array(circle_minimized_values.x[0],
                                    circle_minimized_values.x[1],
                                    x_R,y_R,yaw,correction_factor)
                    
                    Theta_Object.probabilities = data.outputs[ii].probability_distribution
                    Theta_Object.x_center = v0[0]
                    Theta_Object.y_center = v0[1]
                    Theta_Object.r = circle_minimized_values.x[2]
                    Theta_Object.a = 0
                    Theta_Object.b = 0
                    Theta_Object.angle = 0
                    Theta_Object.Final_Likelihood = circle_minimized_values.fun
                    Theta_Object.cls = jj
                    Theta_Object.object_height = object_height
                    # Adding the founded data:
                    Theta_list.object_list.append(Theta_Object)
                    # Making a sum to normalize the probabilities:
                    Norm_factor += circle_minimized_values.fun
                    
                    print ('Found ' + str(counter))
                    
                    
                    
                # Rectangle objects:
                elif jj in A_Rectangle:

                    Theta_Object = Object_Geometry()
                    Theta_Object.height_factor = data.outputs[ii].height_factor
                    if Theta_Object.height_factor == 0:
                        Theta_Object.height_factor = 0.4
                    
                    # Initializing the box array:
                    box = np.array((laser_depth_observations[angle_min:angle_max,:]))

                    bound_a = rospy.get_param('/object_list/o'+str(jj)+'/bound_a')
                    bound_b = rospy.get_param('/object_list/o'+str(jj)+'/bound_b')
                    # Bounds for DE algoritm
                    bounds_R = [ [np.amin(box[:,0])-0.1 , np.amin([np.amax(box[:,0])+0.1 , 3])],
                                 [np.amin(box[:,1])-0.1 , np.amin([np.amax(box[:,1])+0.1 , 3])],
                                 [-np.pi,-0.05],
                                  bound_a,
                                  bound_b]

                    
                    R_class = Likelihood(class_number=jj , Z=box, SSD_probability=SSD_probabilities)
                    # DE angoritm:
                    rectangle_minimized_values = differential_evolution(R_class.probability_for_Rectangle,bounds_R,
                                                                        maxiter = 50,  popsize=9, tol=0.00001)
                    
                    object_height = Object_height_update(Theta_Object.height_factor,
                                                        rectangle_minimized_values.x[3],
                                                        rectangle_minimized_values.x[4],
                                                        rectangle_minimized_values.x[2])
                    # Inserting the founded data:
                    Theta_Object.x_center , Theta_Object.y_center = New_Ce_array(rectangle_minimized_values.x[0],
                                                                                rectangle_minimized_values.x[1],
                                                                                x_R,y_R,yaw,correction_factor)
                    Theta_Object.a = rectangle_minimized_values.x[3]
                    Theta_Object.b = rectangle_minimized_values.x[4]
                    Theta_Object.angle = rectangle_minimized_values.x[2] + yaw
                    Theta_Object.r = 0
                    Theta_Object.cls = jj
                    Theta_Object.Final_Likelihood = rectangle_minimized_values.fun
                    Theta_Object.object_height = object_height
                    # Adding the founded data:
                    Theta_list.object_list.append(Theta_Object)
                    # Making a sum to normalize the probabilities:
                    Norm_factor += rectangle_minimized_values.fun

                    print ('Found ' + str(counter))
                    
                # Elliptical objects:
                elif jj in A_Elliptical:
                    
                    Theta_Object = Object_Geometry()
                    Theta_Object.height_factor = data.outputs[ii].height_factor
                    # Initializing the box array:
                    # If it is a person or dog. the ssd capture much more measurements than it is need to, so:
                    if jj == 15 or jj == 12: 
                        ellipse = np.array((laser_depth_observations[angle_min+7:angle_max-7,:]))
                    else:
                        ellipse = np.array((laser_depth_observations[angle_min:angle_max,:]))
                    #ellipse = np.array((laser_depth_observations[angle_min:angle_max,:]))

                    bound_a = rospy.get_param('/object_list/o'+str(jj)+'/bound_a')
                    bound_b = rospy.get_param('/object_list/o'+str(jj)+'/bound_b')
                    # Bounds for DE algoritm
                    bounds_E = [ [np.amin(ellipse[:,0])-0.1 , np.amin([np.amax(ellipse[:,0])+0.1 , 2])],
                                 [np.amin(ellipse[:,1])-0.1 , np.amin([np.amax(ellipse[:,1])+0.1 , 2])],
                                 [-np.pi,-0.05],
                                  bound_a,
                                  bound_b]

                    E_class = Likelihood(class_number=jj , Z=ellipse , SSD_probability=SSD_probabilities)
                    # DE angoritm:
                    elliptical_minimized_values = differential_evolution(E_class.probability_for_Ellipse,bounds_E,
                                                                            maxiter = 50,  popsize=9, tol=0.00001)

                    object_height = Object_height_update(Theta_Object.height_factor,
                                                2*elliptical_minimized_values.x[3],
                                                2*elliptical_minimized_values.x[4],
                                                elliptical_minimized_values.x[2])
                    # Inserting the founded data:
                    Theta_Object.probabilities = data.outputs[ii].probability_distribution
                    Theta_Object.x_center , Theta_Object.y_center = New_Ce_array(elliptical_minimized_values.x[0] ,elliptical_minimized_values.x[1],x_R,y_R,yaw,correction_factor)
                    Theta_Object.a = elliptical_minimized_values.x[3]
                    Theta_Object.b = elliptical_minimized_values.x[4]
                    Theta_Object.angle = elliptical_minimized_values.x[2] + yaw
                    Theta_Object.r = 0
                    Theta_Object.cls = jj
                    Theta_Object.object_height = object_height
                    Theta_Object.Final_Likelihood = elliptical_minimized_values.fun
                    # Adding the founded data:
                    Theta_list.object_list.append(Theta_Object)
                    # Making a sum to normalize the probabilities:
                    Norm_factor += elliptical_minimized_values.fun
                    print ('Found ' + str(counter))
            finish_time = time.time()
            print ('The time it took was ' + str(np.round(finish_time-start_time,3))+ ' [sec]')
            # Normalize the probabilities:
            for kk in range(0,counter):
                Theta_list.object_list[kk].Final_Likelihood = Theta_list.object_list[kk].Final_Likelihood / Norm_factor
                
            # Adding Mo:
            M_S.M_list.append(Theta_list)  
        # Publishing Mo
        M_list_publisher.publish(M_S)








    
