#include <rclcpp/rclcpp.hpp>
#include <behaviortree_cpp_v3/behavior_tree.h>
#include <behaviortree_cpp_v3/bt_factory.h>
#include <behaviortree_cpp_v3/loggers/bt_zmq_publisher.h>

// --- Action: Stop ---
class Stop : public BT::SyncActionNode
{
public:
  Stop(const std::string & name, const BT::NodeConfiguration & config)
  : BT::SyncActionNode(name, config) {}
  static BT::PortsList providedPorts() { return {}; }
  BT::NodeStatus tick() override {
    RCLCPP_INFO(rclcpp::get_logger("BT"), "Acción: DETENERSE");
    return BT::NodeStatus::SUCCESS;
  }
};

// --- Action: Turn ---
class Turn : public BT::SyncActionNode
{
public:
  Turn(const std::string & name, const BT::NodeConfiguration & config)
  : BT::SyncActionNode(name, config) {}
  static BT::PortsList providedPorts() { return {}; }
  BT::NodeStatus tick() override {
    RCLCPP_INFO(rclcpp::get_logger("BT"), "Acción: GIRAR");
    return BT::NodeStatus::SUCCESS;
  }
};

// --- Action: MoveForward ---
class MoveForward : public BT::SyncActionNode
{
public:
  MoveForward(const std::string & name, const BT::NodeConfiguration & config)
  : BT::SyncActionNode(name, config) {}
  static BT::PortsList providedPorts() { return {}; }
  BT::NodeStatus tick() override {
    RCLCPP_INFO(rclcpp::get_logger("BT"), "Acción: AVANZAR");
    return BT::NodeStatus::SUCCESS;
  }
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = rclcpp::Node::make_shared("bt_robot_node");

  BT::BehaviorTreeFactory factory;

  factory.registerNodeType<Stop>("Stop");
  factory.registerNodeType<Turn>("Turn");
  factory.registerNodeType<MoveForward>("MoveForward");
  factory.registerSimpleCondition("IsObstacleDetected",
    [](BT::TreeNode &) {
      static int count = 0;
      count++;
      if (count % 6 < 3) {
        RCLCPP_INFO(rclcpp::get_logger("BT"), "Condición: HAY obstáculo");
        return BT::NodeStatus::SUCCESS;
      } else {
        RCLCPP_INFO(rclcpp::get_logger("BT"), "Condición: NO hay obstáculo");
        return BT::NodeStatus::FAILURE;
      }
    });

  std::string tree_path = "/home/user/ros2_ws/src/bt_robot/trees/obstacle_tree.xml";
  auto tree = factory.createTreeFromFile(tree_path);

  // Publisher ZMQ para Groot
  BT::PublisherZMQ publisher(tree);

  RCLCPP_INFO(node->get_logger(), "BT iniciado - conecta Groot en puerto 1666");

  rclcpp::Rate rate(1);
  while (rclcpp::ok()) {
    tree.tickRoot();
    rclcpp::spin_some(node);
    rate.sleep();
  }

  rclcpp::shutdown();
  return 0;
}
