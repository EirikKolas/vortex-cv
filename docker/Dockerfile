FROM ros:melodic

ARG distro=melodic
ARG DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"] 

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

# catkin build 
#RUN source /opt/ros/${distro}/setup.bash && \
#    cd ./vortex_ws && \
#    catkin build

#ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]