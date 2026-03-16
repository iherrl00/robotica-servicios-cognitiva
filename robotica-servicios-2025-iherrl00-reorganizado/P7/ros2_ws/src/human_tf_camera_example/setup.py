from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'human_tf_camera_example'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='odiseo',
    maintainer_email='fjrodl@unileon.es',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'static_broadcaster.py = human_tf_camera_example.static_broadcaster:main',
            'human_position_estimator.py = human_tf_camera_example.human_position_estimator:main',
            'human_position_to_baselink.py = human_tf_camera_example.human_position_to_baselink:main',
        ],
    },
)
