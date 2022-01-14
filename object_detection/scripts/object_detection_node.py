#!/usr/bin/env python

import rospy

# Import msg types
from darknet_ros_msgs.msg import BoundingBoxes
from cv_msgs.msg import BBox, BBoxes
from geometry_msgs.msg import PointStamped, PoseStamped
from vortex_msgs.msg import ObjectPosition
from sensor_msgs.msg import PointCloud2, PointField
from sensor_msgs import point_cloud2

# Import classes
from position_estimator import PositionEstimator
from coord_pos import CoordPosition
from pointcloud_mapping import PointCloudMapping

class ObjectDetectionNode():
    """Handles tasks related to object detection
    """
    pointcloud_x = 0.0
    pointcloud_y = 0.0
    pointcloud_z = 0.0

    def __init__(self):
        rospy.init_node('object_detection_node')
        self.bboxSub = rospy.Subscriber('/darknet_ros/bounding_boxes', BoundingBoxes, self.bboxSub_cb)
        self.pcSub = rospy.Subscriber('/zed2/zed_node/point_cloud/cloud_registered', PointCloud2, self.pointcloud_cb)
        self.pcPub = rospy.Publisher('/object_detection/bbox_pointcloud', PointCloud2, queue_size= 1)
        self.estimatorPub = rospy.Publisher('/object_detection/size_estimates', BBoxes, queue_size= 1)
        self.landmarkPub = rospy.Publisher('/object_positions_in',ObjectPosition, queue_size= 1)
        self.position_estimator = PositionEstimator()
        self.coord_positioner = CoordPosition()
        self.pointcloud_mapper = PointCloudMapping()

    def pointcloud_cb(self, msg_data):
        """
        Stores message from a PointCloud2 message into a class variable

        Args:
            msg_data: callback message from subscription

        Returns:
            class variable: self.pointcloud_data
        """
        self.pointcloud_data = msg_data
        self.pointcloud_get_object_with_orientation(msg_data, 0.3) # this is only for testing, the call to this function should be elsewhere. Ideally from a republished poitcloud2 data message callback

    def pointcloud_get_object_with_orientation(self, pointcloud_data, threshold):
        """
        Uses pointcloud data to find object and its orientation in regards to pointcloud_data frame
        
        Args:
            pointcloud_data: The pointcloud data to analyze
            threshold: maximum distance of expected object dimensions as float cm.mm. Ex: if height is bigger than width input height
        """
        assert isinstance(pointcloud_data, PointCloud2)
        pt_gen = point_cloud2.read_points(pointcloud_data)
        closest_point = 200.00
        for pt in pt_gen:
            if abs(pt[2] < closest_point):
                closest_point = abs(pt[2])
        
        object_point_list = []
        pt_gen2 = point_cloud2.read_points(pointcloud_data, skip_nans=True)
        for obj_point in pt_gen2:             
            if abs(obj_point[2]) < (threshold + closest_point):
                object_point_list.append(obj_point)

        eq, fit, errors, residual, middle_point = self.pointcloud_mapper.points_to_plane(object_point_list)
        quaternion_data = fit

        self.send_pose_message(pointcloud_data.header, middle_point, quaternion_data, "middle_pose")
    
    def send_pose_message(self, headerdata, position_data, quaternion_data, name):
        """
        Publishes a PoseStamped as a topic under /object_detection/object_pose

        Args:
            headerdata: Headerdata to be used as a header will not be created in this function
            position_data: A position xyz in the form [x, y, z] where xyz are floats
            quaternion_data: A quaternion wxyz in the form [w, x, y, z]
            name: name to be given to the point published, must not contain special characters.

        Returns:
            Topic:
                /object_detection/object_pose/name where name is your input
        """
        posePub = rospy.Publisher('/object_detection/object_pose/' + name, PoseStamped, queue_size= 1)
        p_msg = PoseStamped()
        # Format header
        p_msg.header = headerdata
        p_msg.header.stamp = rospy.get_rostime()

        # Build pose
        p_msg.pose.position.x = position_data[0]
        p_msg.pose.position.y = position_data[1]
        p_msg.pose.position.z = position_data[2]
        p_msg.pose.orientation.w = quaternion_data[0]
        p_msg.pose.orientation.x = quaternion_data[1]
        p_msg.pose.orientation.y = quaternion_data[2]
        if len(quaternion_data) == 3:
            p_msg.pose.orientation.z = 1
        else:
            p_msg.pose.orientation.z = quaternion_data[3]
        posePub.publish(p_msg)

    def send_pointcloud(self, x_pixel, y_pixel):
        """
        Reads the point cloud data from a given x, y coordinate

        Args:
            x_pixel: position in x direction of point you want clouddata from
            y_pixel: position in y direction of point you want clouddata from

        Returns:
            Point cloud data for a point in the camera frame as list [x, y, z]
        """
        # Generates a readable version of the point cloud data
        is_pointcloud = isinstance(self.pointcloud_data, PointCloud2)
        if is_pointcloud:
            # Reads the point cloud data at given uvs: u = x cord, v = y cord
            pt_gen = point_cloud2.read_points(self.pointcloud_data, skip_nans=False, uvs=[[x_pixel, y_pixel]])
            for pt in pt_gen:
                self.pointcloud_x = pt[0]
                self.pointcloud_y = pt[1]
                self.pointcloud_z = pt[2]

        x, y, z = self.pointcloud_x, self.pointcloud_y, self.pointcloud_z
        return [x, y, z]


    def bboxSub_cb(self, data):
        """
        Gets the data from the subscribed message BoundingBoxes and publishes the size estimates of a detected object, and the position of the object.

        Args:
            data: The message that has been recieved.

        Returns:
            Published topics:
                estimatorPub: Array of detected objects as the estimated size of these. Topic also includes angles to the objects from the camera frame.
        """
        # Allocates msg data to local variables in order to process abs size
        ArrayBoundingBoxes = BBoxes()
        ArrayBoundingBoxes.header = data.header
        ArrayBoundingBoxes.image_header = data.image_header

        # Iterate through all the detected objects and estimate sizes
        for bbox in data.bounding_boxes:
            # Unintuitively position is logged as top to bottom. We fix it so it is from bot to top
            temp_ymin = bbox.ymin
            bbox.ymin = 376 - bbox.ymax
            bbox.ymax = 376 - temp_ymin

            # Store depth measurement of boundingbox
            depth_mtr = bbox.z

            # Get the size estimation from the size estimator class
            object_estimator_data = self.position_estimator.main(bbox)
            redefined_angle_x = object_estimator_data[2]
            redefined_angle_y = object_estimator_data[3]

            # Build the new bounding box message
            CurrentBoundingBox = BBox()
            CurrentBoundingBox.Class = bbox.Class
            CurrentBoundingBox.probability = bbox.probability
            CurrentBoundingBox.width = 0
            CurrentBoundingBox.height = 0
            CurrentBoundingBox.z = depth_mtr
            CurrentBoundingBox.centre_angle_x = redefined_angle_x
            CurrentBoundingBox.centre_angle_y = redefined_angle_y

            # Get the position of the object relative to the camera
            position = self.coord_positioner.main(redefined_angle_x, redefined_angle_y, depth_mtr)

            # Append the new message to bounding boxes array
            ArrayBoundingBoxes.bounding_boxes.append(CurrentBoundingBox)
            
        self.estimatorPub.publish(ArrayBoundingBoxes)

    def rviz_point(self, headerdata, position, name):
        """
        Publishes a PointStamped as a topic under /object_detection/object_point

        Args:
            headerdata: Headerdata to be used as a header will not be created in this function
            position: A position xyz in the form [x, y, z] where xyz are floats
            name: name to be given to the point published, must not contain special characters.

        Returns:
            Topic:
                /object_detection/object_point/name where name is your input
        """
        # For testing
        pointPub = rospy.Publisher('/object_detection/object_point/' + name, PointStamped, queue_size= 1)
        new_point = PointStamped()
        new_point.header = headerdata
        new_point.header.stamp = rospy.get_rostime()
        new_point.point.x = position[0]
        new_point.point.y = position[1]
        new_point.point.z = position[2]
        pointPub.publish(new_point)

    def bboxSub_cb_twin_lense(self, data):
        """
        Gets the data from the subscribed message BoundingBoxes and publishes the size estimates of a detected object, and the position of the object.

        Args:
            data: The message that has been recieved.

        Returns:
            Published topics:
                estimatorPub: Array of detected objects as the estimated size of these. Topic also includes angles to the objects from the camera frame.
                pointPub: A topic is created for each object that is detected. Publishes the point of the object in a coordinate frame.
        """
        # Allocates msg data to local variables in order to process abs size
        ArrayBoundingBoxes = BBoxes()
        ArrayBoundingBoxes.header = data.header
        ArrayBoundingBoxes.image_header = data.image_header

        # Dictionary for saving object to see if the same object is detected twice
        saved_objects = {}

        # Iterate through all the detected objects and estimate sizes
        for bbox in data.bounding_boxes:

            # Store depth measurement of boundingbox
            depth_mtr = bbox.z

            # Get the size estimation from the size estimator class
            position_estimator_data = self.position_estimator.main(bbox)
            length_x_mtr = position_estimator_data[0]
            length_y_mtr = position_estimator_data[1]
            redefined_angle_x = position_estimator_data[2]
            redefined_angle_y = position_estimator_data[3]

            # Build the new bounding box message
            CurrentBoundingBox = BBox()
            CurrentBoundingBox.Class = bbox.Class
            CurrentBoundingBox.probability = bbox.probability
            CurrentBoundingBox.width = length_x_mtr
            CurrentBoundingBox.height = length_y_mtr
            CurrentBoundingBox.z = depth_mtr
            CurrentBoundingBox.centre_angle_x = redefined_angle_x
            CurrentBoundingBox.centre_angle_y = redefined_angle_y

            # Get the position of the object relative to the camera
            position = self.coord_positioner.main(redefined_angle_x, redefined_angle_y, depth_mtr)

            # If the same object is detected in each lense then a point in the middle is calculated
            key_string = str(bbox.Class)
            if (key_string in saved_objects):
                value = saved_objects.get(key_string)
                new_x = (value[0]+position[0])*0.5
                new_y = (value[1]+position[1])*0.5
                new_z = (value[2]+position[2])*0.5
                self.landmarks([new_x,new_y,new_z], key_string)
                saved_objects[str(bbox.Class)] = [new_x, new_y, new_z]
            else:
                saved_objects[str(bbox.Class)] = [position[0], position[1], position[2]]

            self.rviz_point_old(data, saved_objects, key_string)

            # Append the new message to bounding boxes array
            ArrayBoundingBoxes.bounding_boxes.append(CurrentBoundingBox)

        self.estimatorPub.publish(ArrayBoundingBoxes)

    def rviz_point_old(self, data, dictionary, key_string):
        """Delete this when no longer needed"""

        pointPub = rospy.Publisher('/object_detection/object_point/' + key_string, PointStamped, queue_size= 1)
        new_point = PointStamped()
        new_point.header = data.header
        new_point.header.stamp = rospy.get_rostime()
        # new_point.objectID = key_string
        corrected_point = dictionary.get(key_string)
        new_point.point.x = corrected_point[0]
        new_point.point.y = corrected_point[1]
        new_point.point.z = corrected_point[2]
        pointPub.publish(new_point)

    def landmarks(self, position, object_id):
        """
        Builds and sends the ObjectPosition message
        
        Args:
            position: the position in the format of [x, y, z] of the detected object
            object_id: String with name of the object that is detected 

        Returns:
            Published topics:
                landmarkPub: The detected objects position as a landmark.
        """
        landmark = ObjectPosition()
        landmark.objectID = object_id
        landmark.position.x = position[0]
        landmark.position.y = position[1]
        landmark.position.z = position[2]
        self.landmarkPub.publish(landmark)

if __name__ == '__main__':
    node = ObjectDetectionNode()

    while not rospy.is_shutdown():
        rospy.spin()

