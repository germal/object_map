#!/usr/bin/env python

# Libraries:
import rospy
from tf.transformations import quaternion_from_euler
import numpy as np

# msgs:

from object_mapping.msg import Object_Map
from visualization_msgs.msg import Marker , MarkerArray

def callback_map(data):
    global O_map
    O_map = data


rospy.init_node('Points_to_rvis', anonymous=True)

# Publisher:
O_publisher = rospy.Publisher('/Objects' , MarkerArray , queue_size = 5)

#Subsctibers:
M_Subs = rospy.Subscriber('/object_mapped_values',Object_Map,callback_map)
rospy.wait_for_message('/object_mapped_values',Object_Map)

global O_map

A_Round = rospy.get_param('/Array/round')
A_Rectangle = rospy.get_param('/Array/rectangle')
A_Elliptical = rospy.get_param('/Array/elliptical')

while not rospy.is_shutdown():
    M_data = O_map
    list_marker = MarkerArray()
    list_marker.markers = []
    

    for ii in range(len(M_data.object_map)):
        marker = Marker()
        marker_name = Marker()
        # For the angle:
        [x_q,y_q,z_q,w_q] = quaternion_from_euler(0,0,M_data.object_map[ii].angle)

        name = rospy.get_param('/object_list/o'+str(M_data.object_map[ii].cls_num)+'/name')
        
        height_factor = M_data.object_map[ii].height_factor
        
        if height_factor == 0:
            height_factor = 1
        
        if M_data.object_map[ii].cls_num in A_Round:

            # Test for putting a can in the map.
            marker.header.frame_id = 'map'
            marker.header.stamp = rospy.Time.now()
            # Colore of can
            marker.color.r = 0
            marker.color.g = 0
            marker.color.b = 200
            marker.color.a = 1
            # Rest of things:
            marker.id = 1
            marker.type = 3
            marker.action = 0
            marker.lifetime.secs = 0
            # Orientation of the can
            marker.pose.orientation.x = 0
            marker.pose.orientation.y = 0
            marker.pose.orientation.z = 0
            marker.pose.orientation.w = 1
            # Size:        
            marker.scale.x = 2 * M_data.object_map[ii].r
            marker.scale.y = 2 * M_data.object_map[ii].r
            marker.scale.z = height_factor * marker.scale.x
            # Location of the can:
            marker.pose.position.x = M_data.object_map[ii].x_center
            marker.pose.position.y = M_data.object_map[ii].y_center
            #marker.pose.position.z = marker.scale.z/2
            marker.scale.z = M_data.object_map[ii].object_height
            # Name:
            marker.ns = name + str(ii)
            list_marker.markers.append(marker)

            # Text adding:
            marker_name.header.frame_id = 'map'
            marker_name.header.stamp = rospy.Time.now()
            # Orientation of the text
            marker_name.pose.orientation.x = 0
            marker_name.pose.orientation.y = 0
            marker_name.pose.orientation.z = 0
            marker_name.pose.orientation.w = 1
            # Colore of text
            marker_name.color.r = 0
            marker_name.color.g = 0
            marker_name.color.b = 0
            marker_name.color.a = 1
            # Rest of things:
            marker_name.id = 10
            marker_name.type = 9
            marker_name.action = 0
            marker_name.lifetime.secs = 0
            marker_name.pose.position.x = M_data.object_map[ii].x_center
            marker_name.pose.position.y = M_data.object_map[ii].y_center
            marker_name.pose.position.z = 2*marker.pose.position.z + 0.1
            # Size of the text
            marker_name.scale.x = 0.4
            marker_name.scale.y = 0.4
            marker_name.scale.z = 0.4
            marker_name.text = name
            marker_name.ns = name + str(ii)

            list_marker.markers.append(marker_name)
            continue


        
        elif M_data.object_map[ii].cls_num in A_Rectangle:
            # Test for putting a TV in the map.
            marker.header.frame_id = 'map'
            marker.header.stamp = rospy.Time.now()
            # Colour of TV
            marker.color.r = 100
            marker.color.g = 0
            marker.color.b = 100
            marker.color.a = 1
            # Rest of things:
            marker.id = 1
            marker.type = 1
            marker.action = 0
            marker.lifetime.secs = 0
            # Orientation of the TV
            marker.pose.orientation.x = x_q
            marker.pose.orientation.y = y_q
            marker.pose.orientation.z = z_q
            marker.pose.orientation.w = w_q
            # Size:        
            marker.scale.x = M_data.object_map[ii].a
            marker.scale.y = M_data.object_map[ii].b
            angle_O = M_data.object_map[ii].angle
            #marker.scale.z = np.absolute(height_factor * marker.scale.x * np.sin(angle_O))
            marker.scale.z = M_data.object_map[ii].object_height

            # Location of the TV:
            marker.pose.position.x = M_data.object_map[ii].x_center
            marker.pose.position.y = M_data.object_map[ii].y_center
            marker.pose.position.z = marker.scale.z/2
            # Name:
            marker.ns = name + str(ii)
            list_marker.markers.append(marker)

            # Text adding:
            marker_name.header.frame_id = 'map'
            marker_name.header.stamp = rospy.Time.now()
            # Orientation of the text
            marker_name.pose.orientation.x = x_q
            marker_name.pose.orientation.y = y_q
            marker_name.pose.orientation.z = z_q
            marker_name.pose.orientation.w = w_q
            # Colour of text
            marker_name.color.r = 0
            marker_name.color.g = 0
            marker_name.color.b = 0
            marker_name.color.a = 1
            # Rest of things:
            marker_name.id = 10
            marker_name.type = 9
            marker_name.action = 0
            marker_name.lifetime.secs = 0
            marker_name.pose.position.x = M_data.object_map[ii].x_center
            marker_name.pose.position.y = M_data.object_map[ii].y_center
            marker_name.pose.position.z = 2*marker.pose.position.z + 0.1
            # Size of the text
            marker_name.scale.x = 0.4
            marker_name.scale.y = 0.4
            marker_name.scale.z = 0.4
            marker_name.text = name
            marker_name.ns = name + str(ii)

            list_marker.markers.append(marker_name)
            continue

        else:
            # Test for putting an elliptical in the map.
            marker.header.frame_id = 'map'
            marker.header.stamp = rospy.Time.now()
            
            # Rest of things:
            marker.id = 1
            marker.type = 3
            marker.action = 0
            marker.lifetime.secs = 0
            # Orientation of the TV
            marker.pose.orientation.x = x_q
            marker.pose.orientation.y = y_q
            marker.pose.orientation.z = z_q
            marker.pose.orientation.w = w_q
            # Size:        
            marker.scale.x = 2*M_data.object_map[ii].a
            marker.scale.y = 2*M_data.object_map[ii].b
            
            #angle_O = M_data.object_map[ii].angle
            #marker.scale.z = np.absolute(height_factor * marker.scale.x * np.sin(angle_O))
            marker.scale.z = M_data.object_map[ii].object_height

            if M_data.object_map[ii].cls_num == 15:
                marker.scale.z *= 1.4
            # Location of the TV:
            marker.pose.position.x = M_data.object_map[ii].x_center
            marker.pose.position.y = M_data.object_map[ii].y_center
            marker.pose.position.z = marker.scale.z/2
            
            
            marker.color.r = 50
            marker.color.g = 50
            marker.color.b = 100
            marker.color.a = 1
            marker.ns = name + str(ii)
            marker_name.text = name
            marker_name.ns = name + str(ii)
            
            
            list_marker.markers.append(marker)

            # Text adding:
            marker_name.header.frame_id = 'map'
            marker_name.header.stamp = rospy.Time.now()
            # Orientation of the text
            marker_name.pose.orientation.x = x_q
            marker_name.pose.orientation.y = y_q
            marker_name.pose.orientation.z = z_q
            marker_name.pose.orientation.w = w_q
            # Colour of text
            marker_name.color.r = 0
            marker_name.color.g = 0
            marker_name.color.b = 0
            marker_name.color.a = 1
            # Rest of things:
            marker_name.id = 10
            marker_name.type = 9
            marker_name.action = 0
            marker_name.lifetime.secs = 0
            marker_name.pose.position.x = M_data.object_map[ii].x_center
            marker_name.pose.position.y = M_data.object_map[ii].y_center
            marker_name.pose.position.z = 2*marker.pose.position.z + 0.1
            # Size of the text
            marker_name.scale.x = 0.4
            marker_name.scale.y = 0.4
            marker_name.scale.z = 0.4

            list_marker.markers.append(marker_name)
            continue

    #publish:
    O_publisher.publish(list_marker)
    for jj in range(len(list_marker.markers)):
        list_marker.markers[jj].action = 2
            

