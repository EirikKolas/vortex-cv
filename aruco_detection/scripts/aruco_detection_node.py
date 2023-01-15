import rospy
import rospkg

from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image

def callback(data):
    rospy.loginfo(rospy.get_caller_id() + "I heard %s", data.data)
    

class ArucoNode:
    def __init__(self):
        #################
        ###### Node #####
        #################

        #Name of the node
        node_name   = "aruco_detection"
        image_topic = "/zed2/zed_node/rgb/image_rect_color"

        #ROS node init
        rospy.init_node(node_name)

        #Subscribe topic
        self.camSub = rospy.Subscriber(image_topic, Image, self.camera_callback)



        self.bridge = CvBridge()
        


    def camera_callback(self, img_msg):

        try:
            cv_image = self.bridge.imgmsg_to_cv2(img_msg, "passthrough")
        except CvBridgeError as e:
            rospy.logerr("CvBridge Error: {0}".format(e))

        
    ############
    ##Init end##
    ############

if __name__ == '__main__':
    while not rospy.is_shutdown():     
        try:
            aruco = ArucoNode()
            rospy.spin()
        except rospy.ROSInterruptException:
            pass