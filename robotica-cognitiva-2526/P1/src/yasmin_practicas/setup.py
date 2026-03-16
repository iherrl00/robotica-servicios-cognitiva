from setuptools import find_packages, setup

package_name = 'yasmin_practicas'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@todo.todo',
    description='Practicas de YASMIN para Robotica Cognitiva',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'yasmin_demo_ejercicio1 = yasmin_practicas.yasmin_demo_ejercicio1:main',
            'yasmin_demo_ejercicio2 = yasmin_practicas.yasmin_demo_ejercicio2:main',
            'service_client_multi = yasmin_practicas.service_client_multi:main',
            'action_client_monitor = yasmin_practicas.action_client_monitor:main',
            'control_node_yasmin = yasmin_practicas.control_node_yasmin:main',
        ],
    },
)
