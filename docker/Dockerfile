FROM ros:melodic

ARG distro=melodic
ARG DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"] 

###################
## Install stuff ##
###################

#ROS dependencies
RUN apt update && \
    apt install -y --no-install-recommends \
    python-pip \
    python-catkin-tools \
    libx11-dev 

#ROS packages
RUN apt update && \
    apt install -y --no-install-recommends \
    ros-${distro}-tf \
    ros-${distro}-cv-bridge \
    ros-${distro}-image-transport 

#Python dependencies
RUN apt update && \
    apt install -y \
    apt-utils \
    libeigen3-dev \
    libeigen3-dev \
    libglfw3-dev \
    libglew-dev \
    libjsoncpp-dev \
    ros-${distro}-tf \
    ros-${distro}-tf2 \
    libtclap-dev \
    wget \
    nano \ 
    protobuf-compiler \
    python-osrf-pycommon \
    python-openpyxl \
    python-yaml \
    python-enum34 \
    python-pip \
    python-catkin-tools \
    libgeographic-dev \
    ros-${distro}-vision-opencv \
    ros-${distro}-image-transport  \
    ros-${distro}-image-transport-plugins \
    software-properties-common

# pip install
RUN pip install opencv-python==3.4.2.17 && \
    pip install opencv-contrib-python==3.4.2.17


###########
## Build ##
###########

# Assume the root contains vortex-cv, darknet_ros_zed and ddynamic_reconfigure_python
# This is the case when we build using ghcr
COPY ./vortex-cv                    /vortex_ws/src/vortex-cv
COPY ./vortex-msgs                  /vortex_ws/src/vortex-msgs
COPY ./darknet_ros_zed              /vortex_ws/src/darknet_ros_zed
COPY ./ddynamic_reconfigure_python  /vortex_ws/src/ddynamic_reconfigure_python

# catkin build 
RUN source /opt/ros/${distro}/setup.bash && \
    cd ./vortex_ws && \
    catkin build

#ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]