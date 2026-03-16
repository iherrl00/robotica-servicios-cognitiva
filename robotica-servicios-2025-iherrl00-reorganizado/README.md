# ROS2_practicas_iherrl00
# ROS 2 Development Guide

A comprehensive reference guide for working with ROS 2 Jazzy, TurtleSim, Gazebo simulations, and publisher/subscriber communication patterns.

## Table of Contents
- [ROS 2 Installation](#ros-2-installation)
- [Workspace and Package Management](#workspace-and-package-management)
- [TurtleSim Setup](#turtlesim-setup)
- [TurtleBot Setup](#turtlebot-setup)
- [Publisher/Subscriber Packages](#publishersubscriber-packages)
- [Docker Setup](#docker-setup)
- [USB Camera](#usb-camera)
- [Additional Resources](#additional-resources)
- [General Commands](#general-commands)

---

## ROS 2 Installation

### Installing ROS 2 Jazzy on Ubuntu 24.04

Complete installation procedure for ROS 2 Jazzy:

```bash
# Configure locale
locale  # verificar que UTF-8 esté soportado
sudo apt update && sudo apt install locales
sudo locale-gen es_ES es_ES.UTF-8
sudo update-locale LC_ALL=es_ES.UTF-8 LANG=es_ES.UTF-8
export LANG=es_ES.UTF-8

# Add ROS 2 repository
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# Install ROS 2 Jazzy
sudo apt update
sudo apt upgrade
sudo apt install ros-jazzy-desktop

# Configure environment
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
nano ~/.bashrc

# Install development tools
sudo apt install ros-dev-tools
sudo apt install python3-colcon-common-extensions

# Verify installation
which ros2
```

### Testing Installation

```bash
# Source ROS 2
source /opt/ros/jazzy/setup.bash

# Run Zenoh daemon
ros2 run rmw_zenoh_cpp rmw_zenohd

# Terminal 1 - Talker
ros2 run demo_nodes_cpp talker

# Terminal 2 - Listener
ros2 run demo_nodes_py listener
```

---

## Workspace and Package Management

### Creating Workspace and Packages

```bash
# Create workspace
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

# Create C++ package
ros2 pkg create --build-type ament_cmake mi_paquete_c++

# Create Python package
ros2 pkg create --build-type ament_python mi_paquete_python
```

### Building and Running

```bash
# Build packages
cd ~/ros2_ws
colcon build

# Source the workspace
source install/setup.bash

# Run package
ros2 run
```

---

## TurtleSim Setup

### Installation

```bash
# Install TurtleSim
sudo apt update
sudo apt install ros-jazzy-turtlesim

# List available executables
ros2 pkg executables turtlesim
```

### Running TurtleSim

```bash
# Launch simulation node
ros2 run turtlesim turtlesim_node

# Control with keyboard (in another terminal)
ros2 run turtlesim turtle_teleop_key

# Control second turtle
ros2 run turtlesim turtle_teleop_key --ros-args --remap turtle1/cmd_vel:=turtle2/cmd_vel
```

### Useful Commands

```bash
# List nodes
ros2 node list

# List topics
ros2 topic list

# List services
ros2 service list

# List actions
ros2 action list

# Visualize node graph
ros2 run rqt_graph rqt_graph

# Launch RQt
rqt
```

---

## TurtleBot Setup

### Installation and Launch

```bash
# Install TurtleBot4 simulator
sudo apt-get update
sudo apt-get install ros-jazzy-turtlebot4-simulator

# Launch basic simulation
ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py

# Launch with maze world
ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py world:=maze

# Launch with RViz
ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py rviz:=true

# Teleoperación
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Monitor velocity commands
ros2 topic echo /cmd_vel

# Mover y para
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.2}, angular: {z: -0.2}}'
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{}' -1

# (PENDIENTE)
ros2 launch turtlebot.py
```
### ROS2 HUMBLE
```bash
cd robotica-servicios-2025-iherrl00/ros2_ws/src/ROS2andGazebo/Docker
docker compose up
docker exec -it ros2roscon_container bash
sudo apt update
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup -y
sudo apt install ros-humble-turtlebot3* -y
sudo apt install ros-humble-slam-toolbox -y
export TURTLEBOT3_MODEL=waffle
echo "export TURTLEBOT3_MODEL=waffle" >> ~/.bashrc
source ~/.bashrc
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
ros2 topic list
ros2 topic info /scan
ros2 launch nav2_bringup navigation_launch.py use_sim_time:=True
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=True
ros2 run rviz2 rviz2 -d /opt/ros/humble/share/nav2_bringup/rviz/nav2_default_view.rviz
ros2 run teleop_twist_keyboard teleop_twist_keyboard
ros2 run nav2_map_server map_saver_cli -f my_map
ls -lh my_map.*
file my_map.pgm
cat my_map.yaml
```
---

## Publisher/Subscriber Packages

### C++ Package

#### Creating the Package

```bash
# Create workspace and package
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_cmake --license Apache-2.0 cpp_pubsub
```

#### Package Structure

```
cpp_pubsub/
├── CMakeLists.txt
├── package.xml
├── src/
│   ├── publisher_lambda_function.cpp
│   └── subscriber_lambda_function.cpp
└── include/
    └── cpp_pubsub/
```

#### Publisher Implementation

Download the publisher template:

```bash
wget -O publisher_lambda_function.cpp https://raw.githubusercontent.com/ros2/examples/jazzy/rclcpp/topics/minimal_publisher/lambda.cpp
```

Publisher code (src/publisher_lambda_function.cpp):

```cpp
#include <chrono>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

using namespace std::chrono_literals;

class MinimalPublisher : public rclcpp::Node
{
public:
  MinimalPublisher()
  : Node("minimal_publisher"), count_(0)
  {
    publisher_ = this->create_publisher<std_msgs::msg::String>("topic", 10);
    auto timer_callback =
      [this]() -> void {
        auto message = std_msgs::msg::String();
        message.data = "Hello, world! " + std::to_string(this->count_++);
        RCLCPP_INFO(this->get_logger(), "Publishing: '%s'", message.data.c_str());
        this->publisher_->publish(message);
      };
    timer_ = this->create_wall_timer(500ms, timer_callback);
  }

private:
  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
  size_t count_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<MinimalPublisher>());
  rclcpp::shutdown();
  return 0;
}
```

#### Subscriber Implementation

Download the subscriber template:

```bash
wget -O subscriber_lambda_function.cpp https://raw.githubusercontent.com/ros2/examples/jazzy/rclcpp/topics/minimal_subscriber/lambda.cpp
```

Subscriber code (src/subscriber_lambda_function.cpp):

```cpp
#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

class MinimalSubscriber : public rclcpp::Node
{
public:
  MinimalSubscriber()
  : Node("minimal_subscriber")
  {
    auto topic_callback =
      [this](std_msgs::msg::String::UniquePtr msg) -> void {
        RCLCPP_INFO(this->get_logger(), "I heard: '%s'", msg->data.c_str());
      };
    subscription_ =
      this->create_subscription<std_msgs::msg::String>("topic", 10, topic_callback);
  }

private:
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<MinimalSubscriber>());
  rclcpp::shutdown();
  return 0;
}
```

#### CMakeLists.txt Configuration

```cmake
cmake_minimum_required(VERSION 3.8)
project(cpp_pubsub)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

add_executable(talker src/publisher_lambda_function.cpp)
ament_target_dependencies(talker rclcpp std_msgs)

add_executable(listener src/subscriber_lambda_function.cpp)
ament_target_dependencies(listener rclcpp std_msgs)

install(TARGETS
  talker
  listener
  DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
```

#### package.xml Configuration

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>cpp_pubsub</name>
  <version>0.0.0</version>
  <description>TODO: Package description</description>
  <maintainer email="isabella-herrarte@todo.todo">isabella-herrarte</maintainer>
  <license>Apache-2.0</license>

  <buildtool_depend>ament_cmake</buildtool_depend>
  <depend>rclcpp</depend>
  <depend>std_msgs</depend>

  <test_depend>ament_lint_auto</test_depend>
  <test_depend>ament_lint_common</test_depend>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
```

#### Building and Running

```bash
# Navigate to workspace
cd ~/ros2_ws

# Install dependencies
rosdep install -i --from-path src --rosdistro jazzy -y

# Build the package
colcon build --packages-select cpp_pubsub

# Source the workspace
source install/setup.bash

# Terminal 1 - Run publisher
ros2 run cpp_pubsub talker

# Terminal 2 - Run subscriber
ros2 run cpp_pubsub listener
```

---

### Python Package

#### Creating the Package

```bash
# Create Python package
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_python --license Apache-2.0 py_pubsub
```

#### Package Structure

```
py_pubsub/
├── package.xml
├── setup.py
├── setup.cfg
├── test/
├── resource/
│   └── py_pubsub
└── py_pubsub/
    ├── __init__.py
    ├── publisher_member_function.py
    └── subscriber_member_function.py
```

#### Publisher Implementation

Download the publisher template:

```bash
wget https://raw.githubusercontent.com/ros2/examples/jazzy/rclpy/topics/minimal_publisher/examples_rclpy_minimal_publisher/publisher_member_function.py
```

#### Subscriber Implementation

Download the subscriber template:

```bash
wget https://raw.githubusercontent.com/ros2/examples/jazzy/rclpy/topics/minimal_subscriber/examples_rclpy_minimal_subscriber/subscriber_member_function.py
```

#### setup.py Configuration

Update the `entry_points` section:

```python
entry_points={
    'console_scripts': [
        'talker = py_pubsub.publisher_member_function:main',
        'listener = py_pubsub.subscriber_member_function:main',
    ],
},
```

#### Building and Running

```bash
# Install dependencies
rosdep install -i --from-path src --rosdistro jazzy -y

# Build the package
colcon build --packages-select py_pubsub

# Source the workspace
source install/setup.bash

# Terminal 1 - Run publisher
ros2 run py_pubsub talker

# Terminal 2 - Run subscriber
ros2 run py_pubsub subscriber
```

---

## Docker Setup

### Running ROS 2 with VNC Desktop

```bash
# Run with VNC access on port 6080
docker run -p 6080:80 --security-opt seccomp=unconfined --shm-size=512m \
  ghcr.io/tiryoh/ros2-desktop-vnc:humble
```

Access the desktop at: `http://localhost:6080`

---

### Instalación y Configuración
```bash
# Clonar repositorio
cd ~
git clone https://github.com/fjrodl/ROS2andGazebo.git

# Docker (alternativa)
cd ROSConES/Docker
docker build -t ros2roscon .
docker compose up
docker exec -it ros2roscon_container bash
docker context use default
docker context ls

# Compilar workspace
colcon build --symlink-install
source /opt/ros/humble/setup.bash
```

### Comandos Básicos de Gazebo
```bash
# Iniciar Gazebo
ign gazebo
ign gazebo empty.sdf

# Comandos de topics
ign topic -l
ign topic -i -t /topic_name
ign topic -e -t /topic_name
ign topic -e -t cube_camera/camera_info
```

### Key Publisher Plugin
```bash
# Abrir Gazebo
ign gazebo empty.sdf

# Verificar topics
ign topic -l

# Escuchar teclas
ign topic -e -t /keyboard/keypress
```

### Spawn de Objetos
```bash
# Crear paquete
ros2 pkg create spawn_simple_object --dependencies xacro
cd spawn_simple_object
mkdir launch urdf
cd urdf
nano cube.urdf.xacro

# Compilar y lanzar
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 launch spawn_simple_object spawn_model.launch.py
```

### Sensores en Gazebo
```bash
# Instalar dependencias
sudo apt-get install ros-humble-realsense2-camera
sudo apt-get install ros-humble-realsense2-description

# Crear paquete
ros2 pkg create gazebo_sensors --dependencies xacro realsense2_description
cd gazebo_sensors
mkdir urdf launch
touch urdf/cube_with_sensors.urdf.xacro
touch launch/cube_with_sensors.launch.py

# Visualización
sudo apt-get install ros-humble-rqt-*
ros2 run rqt_image_view rqt_image_view
rviz2
```

### ROS2 Bridge
```bash
# Bridge general
ros2 run ros_gz_bridge parameter_bridge /TOPIC@ROS_MSG@GZ_MSG

# Ejemplo CameraInfo
ros2 run ros_gz_bridge parameter_bridge /cube_camera/camera_info@sensor_msgs/msg/CameraInfo@ignition.msgs.CameraInfo

# Key Publisher Bridge
ign topic -i -t /keyboard/keypress
ros2 run ros_gz_bridge parameter_bridge /keyboard/keypress@std_msgs/msg/Int32[ignition.msgs.Int32
ros2 topic echo /keyboard/keypress

# Bridge de sensores
ros2 launch gazebo_sensors cube_with_sensors.launch.py
ros2 launch gazebo_sensors gazebo_bridge.launch.py

# Verificar tipos
ign topic -i -t /cube_camera/camera_info
ign topic -i -t /cube_camera/image_raw
ign topic -i -t /cube_depth/image_raw/points
ign topic -i -t /lidar
```

### ROBOT Differential Drive
```bash
# Crear paquete
ros2 pkg create diff_drive_description --dependencies xacro
cd diff_drive_description
mkdir urdf launch
nano urdf/diff_drive.urdf.xacro
nano urdf/diff_drive_macro.xacro
nano launch/diff_drive.launch.py

# Compilar y lanzar
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 launch diff_drive_description diff_drive.launch.py

# Controlar robot
rqt
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}, angular: {z: 0.5}}"
```

### Plugins Personalizados
```bash
# Crear estructura
mkdir hello_world && cd hello_world
nano HelloWorld.cpp
nano CMakeLists.txt
nano hello_world_plugin.sdf

# Compilar
mkdir build && cd build
cmake ..
make

# Exportar ruta
export GZ_SIM_SYSTEM_PLUGIN_PATH=`pwd`/build

# Lanzar
ign gazebo -v 3 hello_world_plugin.sdf
```

### Launch Files
```bash
# Lanzar launch file
ros2 launch paquete archivo.launch.py
ros2 launch diff_drive_description diff_drive.launch.py
```

### Verificar
```bash
# Verificar topics ROS 2
ros2 topic list
ros2 topic echo /topic_name
ros2 topic echo /cube_camera/camera_info
ros2 topic info /topic_name
ros2 topic hz /topic_name

# Verificar nodos
ros2 node list
ros2 node info /node_name

# Verificar transformadas
ros2 run tf2_tools view_frames
ros2 run tf2_ros tf2_echo frame1 frame2
ros2 run tf2_ros tf2_echo base_link lidar_link

# Logs de Gazebo
ign gazebo -v 3 world.sdf
ign gazebo -v 4 world.sdf
```

### COMANDOS ESENCIALES GAZEBO (RESUMEN)
```bash
# Gazebo
ign gazebo empty.sdf
ign topic -l
ign topic -e -t /topic_name

# Compilar
colcon build --symlink-install
source install/setup.bash

# Bridge
ros2 run ros_gz_bridge parameter_bridge /topic@ROS_MSG@GZ_MSG

# Control de robot
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}}"

# Visualización
rviz2
ros2 run rqt_image_view rqt_image_view

# Debugging
ros2 topic list
ros2 topic echo /topic_name
ros2 node list
```

### Portainer
```bash
docker volume create portainer_data
docker run -d -p 8000:8000 -p 9443:9443 --name portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce:lts
```
Access the desktop at: `http://localhost:9443

## USB Camera

### Running USB Camera Node

```bash
# Run basic USB camera node
ros2 run usb_cam usb_cam_node_exe

# Run with parameters file
ros2 run usb_cam usb_cam_node_exe --ros-args --params-file ~/ros2_ws/src/usb_cam/config/params.yaml

# Launch camera
ros2 launch usb_cam camera.launch.py

# Run first camera with namespace
ros2 run usb_cam usb_cam_node_exe --ros-args --remap __ns:=/usb_cam_0 --params-file ~/ros2_ws/src/usb_cam/config/params_1.yaml

# Run second camera with namespace
ros2 run usb_cam usb_cam_node_exe --ros-args --remap __ns:=/usb_cam_1 --params-file ~/ros2_ws/src/usb_cam/config/params_2.yaml
```

---

## Additional Resources

### Official Documentation

- [ROS 2 Jazzy Installation](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)
- [Gazebo Integration](https://docs.ros.org/en/jazzy/Tutorials/Advanced/Simulators/Gazebo/Gazebo.html)
- [TurtleSim Tutorial](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Introducing-Turtlesim/Introducing-Turtlesim.html)
- [C++ Publisher/Subscriber](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Cpp-Publisher-And-Subscriber.html)
- [Python Publisher/Subscriber](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.html)
- [Python Service/Client](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Service-And-Client.html)

### External Resources

- [Docker ROS Images](https://hub.docker.com/_/ros/)
- [ROS Desktop VNC](https://hub.docker.com/r/tiryoh/ros2-desktop-vnc)
- [Portainer](https://docs.portainer.io/start/install-ce/server/docker/linux)
- [USB Camera Driver](https://github.com/ros-drivers/usb_cam)

---

## General Commands

### Gazebo Installation

```bash
# Install Gazebo integration
sudo apt update
sudo apt install ros-jazzy-ros-gz

# Launch Gazebo simulator
gz sim
```

### Version Control with vcstool

```bash
# Install vcstool
sudo apt install python3-vcstool
sudo apt update
sudo apt upgrade python3-vcstool

# Import repositories
cd ~/ros2_ws
vcs import src < PATH_TO_ROSINSTALL_FILE.rosinstall

# Update repositories
vcs pull src
```

### General Shell Commands

```bash
# Create directory
mkdir <directory_name>

# Change directory
cd <directory_name>

# Build with CMake
cmake ..
make

# Edit files
nano

# Git operations
git add .
git commit -m "mensaje"
git pull --rebase origin main
git push origin main
```

---

## Notes

- Always source your workspace after building: `source install/setup.bash`
- Use `colcon build --packages-select <package_name>` to build specific packages
- The default VNC password for Docker images is typically `headless`
- Adjust `--shm-size` parameter if experiencing display issues with Docker

---

**Last Updated:** October 2025
