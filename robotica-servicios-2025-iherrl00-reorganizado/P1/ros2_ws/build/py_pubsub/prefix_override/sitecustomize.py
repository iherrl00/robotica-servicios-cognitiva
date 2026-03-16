import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/isabella-herrarte/robotica-servicios-2025-iherrl00-reorganizado/P1/ros2_ws/install/py_pubsub'
