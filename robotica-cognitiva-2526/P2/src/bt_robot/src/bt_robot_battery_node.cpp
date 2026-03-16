#include <rclcpp/rclcpp.hpp>
#include <behaviortree_cpp_v3/behavior_tree.h>
#include <behaviortree_cpp_v3/bt_factory.h>
#include <behaviortree_cpp_v3/loggers/bt_zmq_publisher.h>

// --- Condition: ¿Batería baja? ---
class IsBatteryLow : public BT::ConditionNode
{
public:
  IsBatteryLow(const std::string & name) : BT::ConditionNode(name, {}) {}
  BT::NodeStatus tick() override {
    static int count = 0;
    count++;
    // Simula batería baja cada 10 ticks
    if (count % 10 >= 7) {
      RCLCPP_INFO(rclcpp::get_logger("BT"), "Condición: BATERÍA BAJA");
      return BT::NodeStatus::SUCCESS;
    }
    RCLCPP_INFO(rclcpp::get_logger("BT"), "Condición: batería OK");
    return BT::NodeStatus::FAILURE;
  }
};

// --- Condition: ¿Batería OK? ---
class IsBatteryOK : public BT::ConditionNode
{
public:
  IsBatteryOK(const std::string & name) : BT::ConditionNode(name, {}) {}
  BT::NodeStatus tick() override {
    static int count = 0;
    count++;
    if (count % 10 < 7) {
      return BT::NodeStatus::SUCCESS;
    }
    return BT::NodeStatus::FAILURE;
  }
};

// --- Condition: ¿Hay obstáculo? ---
class IsObstacleDetected : public BT::ConditionNode
{
public:
  IsObstacleDetected(const std::string & name) : BT::ConditionNode(name, {}) {}
  BT::NodeStatus tick() override {
    static int count = 0;
    count++;
    if (count % 6 < 3) {
      RCLCPP_INFO(rclcpp::get_logger("BT"), "Condición: HAY obstáculo");
      return BT::NodeStatus::SUCCESS;
    }
    RCLCPP_INFO(rclcpp::get_logger("BT"), "Condición: NO hay obstáculo");
    return BT::NodeStatus::FAILURE;
  }
};

// --- Action: Volver a base ---
class ReturnToBase : public BT::SyncActionNode
{
public:
  ReturnToBase(const std::string & name, const BT::NodeConfiguration & config)
  : BT::SyncActionNode(name, config) {}
  static BT::PortsList providedPorts() { return {}; }
  BT::NodeStatus tick() override {
    RCLCPP_INFO(rclcpp::get_logger("BT"), "Acción: VOLVER A BASE");
    return BT::NodeStatus::SUCCESS;
  }
};

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

// --- Action: NavigateToWaypoint ---
class NavigateToWaypoint : public BT::SyncActionNode
{
public:
  NavigateToWaypoint(const std::string & name, const BT::NodeConfiguration & config)
  : BT::SyncActionNode(name, config) {}
  static BT::PortsList providedPorts() { return {}; }
  BT::NodeStatus tick() override {
    RCLCPP_INFO(rclcpp::get_logger("BT"), "Acción: NAVEGAR A WAYPOINT");
    return BT::NodeStatus::SUCCESS;
  }
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = rclcpp::Node::make_shared("bt_robot_battery_node");

  BT::BehaviorTreeFactory factory;

  factory.registerNodeType<Stop>("Stop");
  factory.registerNodeType<Turn>("Turn");
  factory.registerNodeType<NavigateToWaypoint>("NavigateToWaypoint");
  factory.registerNodeType<ReturnToBase>("ReturnToBase");
  factory.registerSimpleCondition("IsBatteryLow",
    [](BT::TreeNode &) {
      static int count = 0; count++;
      if (count % 10 >= 7) {
        RCLCPP_INFO(rclcpp::get_logger("BT"), "BATERÍA BAJA → volviendo a base");
        return BT::NodeStatus::SUCCESS;
      }
      return BT::NodeStatus::FAILURE;
    });
  factory.registerSimpleCondition("IsBatteryOK",
    [](BT::TreeNode &) {
      static int count = 0; count++;
      return (count % 10 < 7) ? BT::NodeStatus::SUCCESS : BT::NodeStatus::FAILURE;
    });
  factory.registerSimpleCondition("IsObstacleDetected",
    [](BT::TreeNode &) {
      static int count = 0; count++;
      if (count % 6 < 3) {
        RCLCPP_INFO(rclcpp::get_logger("BT"), "HAY obstáculo");
        return BT::NodeStatus::SUCCESS;
      }
      RCLCPP_INFO(rclcpp::get_logger("BT"), "NO hay obstáculo");
      return BT::NodeStatus::FAILURE;
    });

  std::string tree_path = "/home/user/ros2_ws/src/bt_robot/trees/service_robot_tree.xml";
  auto tree = factory.createTreeFromFile(tree_path);

  BT::PublisherZMQ publisher(tree);

  RCLCPP_INFO(node->get_logger(), "BT con batería iniciado - conecta Groot en puerto 1666");

  rclcpp::Rate rate(1);
  while (rclcpp::ok()) {
    tree.tickRoot();
    rclcpp::spin_some(node);
    rate.sleep();
  }

  rclcpp::shutdown();
  return 0;
}
