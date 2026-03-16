cmake_minimum_required(VERSION 3.8)
project(bt_robot)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(behaviortree_cpp_v3 REQUIRED)

add_executable(bt_robot_node src/bt_robot_node.cpp)
ament_target_dependencies(bt_robot_node rclcpp behaviortree_cpp_v3)

add_executable(bt_robot_battery_node src/bt_robot_battery_node.cpp)
ament_target_dependencies(bt_robot_battery_node rclcpp behaviortree_cpp_v3)

install(TARGETS
  bt_robot_node
  bt_robot_battery_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY trees
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
