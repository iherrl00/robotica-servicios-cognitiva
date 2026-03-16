from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'navegacion_avanzada'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Archivos de configuración
        (os.path.join('share', package_name, 'config'), 
            glob('config/*.yaml')),
        # Launch files (si los creas)
        (os.path.join('share', package_name, 'launch'), 
            glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Isabella Herrarte',
    maintainer_email='iherrl00@estudiantesunileon.es',
    description='Navegación avanzada con Nav2, voz y múltiples planificadores',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'waypoint_navigator = navegacion_avanzada.waypoint_navigator:main',
            'planner_changer = navegacion_avanzada.planner_changer:main',
            'waypoint_navigator_voice = navegacion_avanzada.waypoint_navigator_voice:main',
            'waypoint_navigator_voice_planner_change = navegacion_avanzada.waypoint_navigator_voice_planner_change:main',
	        # Nodos nuevos (arquitectura múltiples nodos)
            'control_node = navegacion_avanzada.control_node:main',
            'navigation_node = navegacion_avanzada.navigation_node:main',
            'dialogue_node = navegacion_avanzada.dialogue_node:main',
            'control_node_fixed = navegacion_avanzada.control_node_v3:main',
            'navigation_node_fixed = navegacion_avanzada.navigation_node_v2:main',
            'dialogue_node_fixed = navegacion_avanzada.dialogue_node_v3:main',
            'control_node_yasmin = navegacion_avanzada.control_node_yasmin:main',
            'navigation_node_yasmin = navegacion_avanzada.navigation_node_yasmin:main',
        ],
    },
)
