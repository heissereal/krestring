#!/usr/bin/env python

import rospy
import math
import tf
from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import Vector3
from std_msgs.msg import Float64
from sensor_msgs.msg import Joy
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from sensor_msgs.msg import JointState

class dynamixelInterface:
    def __init__(self):
        self.pose = PoseStamped()
        self.mocap_sub = rospy.Subscriber("mocap/pose", PoseStamped, self.mocapCallback)
        self.joy = Joy()
        self.joy_state_x = 0.0
        self.joy_state_y = 0.0
        self.joy_sub = rospy.Subscriber("joy", Joy, self.joyCallback)
        self.euler_vec = Vector3()

        self.degree = 20.0/180.0*math.pi
        self.servo0_degree = self.degree
        self.servo1_degree = self.degree
        self.servo2_degree = self.degree
        self.servo3_degree = self.degree
        
        #self.position_list = [60.0/180.0*math.pi]
        #self.cnt = 0
        self.count = 0
        self.downcount = 12
        self.i = 0
        self.trajectory_pub = rospy.Publisher("dynamixel_workbench/joint_trajectory", JointTrajectory, queue_size=1)
        self.trajectory_msg = JointTrajectory()
        self.trajectory_msg.points = [None]
        self.trajectory_point = JointTrajectoryPoint()

        self.initial_position = [0] * 4
        self.initialized_flag = False
        self.joint_state_sub = rospy.Subscriber("dynamixel_workbench/joint_states", JointState, self.jointStateCallback)        

        self.timer = rospy.Timer(rospy.Duration(1.0), self.timerCallback)



    def mocapCallback(self, msg):
        self.pose = msg

    def joyCallback(self, msg):
        self.joy = msg
    def joy_state(self):
        self.joy_state_x = self.joy.axes[0]
        self.joy_state_y = self.joy.axes[1]
        print("joy_state x :{} y:{} ".format(self.joy_state_x, self.joy_state_y))

    def quaternion_to_euler(self):
        quaternion_x = self.pose.pose.orientation.x
        quaternion_y = self.pose.pose.orientation.y
        quaternion_z = self.pose.pose.orientation.z
        quaternion_w = self.pose.pose.orientation.w
        euler = tf.transformations.euler_from_quaternion((quaternion_x,quaternion_y,quaternion_z,quaternion_w))
        self.euler_vec.x = euler[0]
        self.euler_vec.y = euler[1]
        self.euler_vec.z = euler[2]
        print("euler: {}, {}, {}".format(self.euler_vec.x, self.euler_vec.y, self.euler_vec.z))


    def P_control(self):
        Kp = 0.5
        output_x = - self.euler_vec.x * Kp
        output_y = - self.euler_vec.y * Kp

        self.servo0_degree = self.degree - output_y
        self.servo1_degree = self.degree - output_x
        self.servo2_degree = self.degree + output_y
        self.servo3_degree = self.degree + output_x
        #rospy.loginfo(output_x)
        #rospy.loginfo(output_y)
        print("degree: {}, {}, {}, {}".format(self.servo0_degree, self.servo1_degree, self.servo2_degree, self.servo3_degree))
        
    def timerCallback(self, event):
        self.joy_state()
        self.quaternion_to_euler()
        self.P_control()
        # self.cnt = (self.cnt + 1) % len(self.position_list)
        self.count = self.count + 1
        self.trajectory_msg.joint_names = ['servo0', 'servo1','servo2', 'servo3']
        if self.count <= 12:
            self.trajectory_point.positions = [self.servo0_degree *self.count + self.initial_position[0], -self.servo1_degree*self.count + self.initial_position[1], self.servo2_degree*self.count + self.initial_position[2], -self.servo3_degree*self.count + self.initial_position[3]]
        elif self.count >= 12 and self.count <= 24:
            self.downcount = self.downcount - 1
            self.trajectory_point.positions = [self.servo0_degree *self.downcount + self.initial_position[0], -self.servo1_degree*self.downcount + self.initial_position[1], self.servo2_degree*self.downcount + self.initial_position[2], -self.servo3_degree*self.downcount + self.initial_position[3]]
        else:
            self.trajectory_point.positions = [self.initial_position[0],self.initial_position[1],self.initial_position[2],self.initial_position[3]]

        #self.trajectory_point.positions = [self.position_list[self.cnt], self.position_list[self.cnt], self.position_list[self.cnt], self.position_list[self.cnt]]
        self.trajectory_point.velocities = [0.0,0.0,0.0,0.0]
        self.trajectory_point.accelerations = [0.0, 0.0,0.0,0.0]
        self.trajectory_point.effort = [0.0, 0.0,0.0,0.0]
        self.trajectory_point.time_from_start = rospy.Time(0.1)

        self.trajectory_msg.points[0] = self.trajectory_point
        self.trajectory_pub.publish(self.trajectory_msg)

    def jointStateCallback(self, msg):
        if not self.initialized_flag:
            for i in range(len(self.initial_position)):
                self.initial_position[i] = msg.position[i]
            self.initialized_flag = True

if __name__ == '__main__':
    rospy.init_node("dynamixel_interface_node")
    node = dynamixelInterface()
    rospy.spin()
