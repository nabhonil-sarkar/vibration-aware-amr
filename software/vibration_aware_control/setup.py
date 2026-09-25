from glob import glob
from setuptools import setup, find_packages

setup(
    name='vibration_aware_control', version='0.1.0',
    packages=find_packages(exclude=['tests']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/vibration_aware_control']),
        ('share/vibration_aware_control', ['package.xml', 'README.md']),
        ('share/vibration_aware_control/config', glob('config/*.yaml')),
        ('share/vibration_aware_control/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'], zip_safe=True,
    maintainer='Nabhonil Sarkar', maintainer_email='nabhonil@example.invalid',
    description='Prototype payload-vibration-aware velocity adaptation',
    license='Proprietary',
    entry_points={'console_scripts': [
        'vibration_controller = vibration_aware_control.ros_node:main',
        'vibration_demo = vibration_aware_control.demo:main',
    ]},
)
