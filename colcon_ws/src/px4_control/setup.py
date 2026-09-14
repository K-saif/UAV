from setuptools import find_packages, setup

package_name = 'px4_control'

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
    maintainer='khans',
    maintainer_email='khans@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
		'square_mission = px4_control.square_mission:main',
        'square_mission_sr = px4_control.square_mission_sr:main',
        'gesture_camera = px4_control.gesture_camera:main',
        'drone_camera_viewer = px4_control.drone_camera_viewer:main',
        'ai_target_follower = px4_control.ai_target_follower:main'
        ],
    },
)
