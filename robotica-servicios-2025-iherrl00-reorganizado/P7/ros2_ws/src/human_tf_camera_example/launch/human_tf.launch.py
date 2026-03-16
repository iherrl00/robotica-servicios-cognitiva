from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='v4l2_camera',
            executable='v4l2_camera_node',
            name='laptop_camera',
            output='screen'
        ),
        Node(
            package='human_tf_camera_example',
            executable='static_broadcaster.py',
            name='camera_tf_broadcaster',
            output='screen'
        ),
        Node(
            package='human_tf_camera_example',
            executable='human_position_estimator.py',
            name='human_estimator',
            output='screen'
        ),
        # Esperar 5 segundos antes de lanzar el listener
        TimerAction(
            period=5.0,
            actions=[
                Node(
                    package='human_tf_camera_example',
                    executable='human_position_to_baselink.py',
                    name='human_to_baselink',
                    output='screen'
                )
            ]
        )
    ])
