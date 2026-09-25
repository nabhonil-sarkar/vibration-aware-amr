"""ROS 2 adapter. Safety watchdogs use wall-monotonic time, even in simulation."""
from dataclasses import asdict
import json
import math
import time

import rclpy
from rclpy.node import Node
from rclpy.clock import Clock, ClockType
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, qos_profile_sensor_data
from geometry_msgs.msg import Twist, TwistStamped
from sensor_msgs.msg import Imu
from std_msgs.msg import String
from std_srvs.srv import SetBool

from .core import Config, Controller


class VibrationNode(Node):
    def __init__(self):
        super().__init__('vibration_controller')
        parameters = {}
        for name, default in asdict(Config()).items():
            parameters[name] = self.declare_parameter(name, default).value
        self.core = Controller(Config(**parameters))
        self.stamped = self.declare_parameter('stamped_commands', True).value
        self.imu_frame = self.declare_parameter('imu_frame', 'payload_imu_link').value
        self.command_frame = self.declare_parameter('command_frame', 'base_link').value
        self.max_age = self.declare_parameter('max_header_age_s', 0.15).value
        if not math.isfinite(self.max_age) or self.max_age <= 0:
            raise ValueError('max_header_age_s must be positive')
        self.last_imu_stamp = None
        self.last_cmd_stamp = None
        message_type = TwistStamped if self.stamped else Twist
        command_qos = QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=1,
                                 reliability=ReliabilityPolicy.RELIABLE)
        self.publisher = self.create_publisher(message_type, 'cmd_vel_vibration', command_qos)
        self.status_pub = self.create_publisher(String, 'vibration/status', 10)
        self.create_subscription(message_type, 'cmd_vel_requested', self.command_callback, command_qos)
        self.create_subscription(Imu, 'payload/imu', self.imu_callback, qos_profile_sensor_data)
        self.create_service(SetBool, 'vibration/enable', self.enable_callback)
        self.timer = self.create_timer(0.02, self.tick, clock=Clock(clock_type=ClockType.STEADY_TIME))
        self.status_count = 0
        self.get_logger().warning('Prototype DISABLED. Thresholds need measurement. Independent E-stop required.')

    def check_header(self, header, expected_frame, previous):
        stamp = header.stamp.sec * 1_000_000_000 + header.stamp.nanosec
        age = (self.get_clock().now().nanoseconds - stamp) / 1e9
        valid = (stamp > 0 and (previous is None or stamp > previous) and
                 -0.02 <= age <= self.max_age and header.frame_id == expected_frame)
        return valid, stamp

    def imu_callback(self, msg):
        valid, stamp = self.check_header(msg.header, self.imu_frame, self.last_imu_stamp)
        if not valid or msg.linear_acceleration_covariance[0] == -1:
            self.core.invalidate_imu('imu_header_or_covariance_fault')
            self.last_imu_stamp = None
            return
        self.last_imu_stamp = stamp
        a = msg.linear_acceleration
        self.core.feed_imu((a.x, a.y, a.z), time.monotonic())

    def command_callback(self, msg):
        if self.stamped:
            valid, stamp = self.check_header(msg.header, self.command_frame, self.last_cmd_stamp)
            if not valid:
                self.core.command_time = None
                self.core.stop('command_header_fault')
                self.last_cmd_stamp = None
                return
            self.last_cmd_stamp = stamp
            msg = msg.twist
        # This controller only supports planar, non-holonomic velocity commands.
        unused = (msg.linear.y, msg.linear.z, msg.angular.x, msg.angular.y)
        if any(not math.isfinite(x) or abs(x) > 1e-9 for x in unused):
            self.core.command_time = None
            self.core.stop('unsupported_command_axes')
            return
        self.core.feed_command(msg.linear.x, msg.angular.z, time.monotonic())

    def enable_callback(self, request, response):
        if request.data:
            response.success = self.core.enable(time.monotonic())
        else:
            self.core.stop('disabled_by_operator')
            self.publish_command(0.0, 0.0)
            response.success = True
        response.message = self.core.reason
        return response

    def publish_command(self, v, w):
        output = TwistStamped() if self.stamped else Twist()
        twist = output.twist if self.stamped else output
        if self.stamped:
            output.header.stamp = self.get_clock().now().to_msg()
            output.header.frame_id = self.command_frame
        twist.linear.x = v
        twist.angular.z = w
        self.publisher.publish(output)

    def tick(self):
        self.publish_command(*self.core.step(time.monotonic()))
        self.status_count += 1
        if self.status_count % 5 == 0:
            self.status_pub.publish(String(data=json.dumps(self.core.status(), allow_nan=False)))


def main(args=None):
    rclpy.init(args=args)
    node = VibrationNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node.publish_command(0.0, 0.0)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
