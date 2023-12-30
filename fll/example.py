from hub import light_matrix, sound, port, motion_sensor
import runloop
import color_sensor
import motor
import motor_pair
import device
import color
import time


# DEFAULT PARAMETERS
# Default motor turning speed
DEFAULT_SPEED = 20 # degrees per second
PI = 3.1415926
TURN_FACTOR = 1.638
WHEEL_DIAMETER = 8.79
BLACK_REFLECTION = 35
WHITE_REFLECTION = 99
MEDIUM_REFLECTION = (99 + 35) / 2


# Two-wheel motor setup
# Assuming ports connected: A, E
motor_pair.pair(motor_pair.PAIR_1, port.A, port.E)
MOVE_PAIR = motor_pair.PAIR_1
LEFT_MOTOR = port.A


# Attachment motor setup
ARM_1_MOTOR_PORT = port.D


# Global checking
assert device.ready(port.A)
assert device.ready(port.E)
assert device.ready(port.D)


#########################
# Basic Movement
#########################

async def move(how: str = "forward", distance: float = 100, speed: float = 20):
    """Move straight forward/backward.
    Args:
        how: "forward" or "backward", default="forward"
        distance: move distance in cm
        speed: speed cm/s
        wheel_diameter: edge to edge diameter in cms
    """
    print("Move {} for {} cm with speed {} cm/s.".format(how, distance, speed))
    assert (how in ["forward", "backward"])
    if how == "forward":
        light_matrix.show_image(light_matrix.IMAGE_ARROW_E)
    else:
        light_matrix.show_image(light_matrix.IMAGE_ARROW_W)
    factor = 1.0 / (PI * WHEEL_DIAMETER) * 360
    degrees_to_rotate = int(distance * factor)
    rotate_speed = int(speed * factor)
    rotate_speed = rotate_speed if how == "forward" else -rotate_speed
    await motor_pair.move_for_degrees(MOVE_PAIR, degrees_to_rotate, 0, velocity=rotate_speed)
    light_matrix.clear()


async def turn(how: str = "left", degrees: float = 90, speed: float = 10, turn_factor: float = TURN_FACTOR):
    """Make a turn.
    Args:
        how: "left" or "right"
        degrees: degrees to turn
        turn_factor: factor to convert turn degrees to motor movements.
        speed: degrees per sec
    """
    print("Turn {} for {} degrees with speed {} degrees/s and turn_factor {}.".format(how, degrees, speed, turn_factor))
    assert (how in ["left", "right"])
    if how == "left":
        light_matrix.show_image(light_matrix.IMAGE_ARROW_N)
    else:
        light_matrix.show_image(light_matrix.IMAGE_ARROW_S)
    degrees_to_rotate = int(degrees * turn_factor)
    rotate_speed = int(speed * turn_factor * 10)
    direction = -rotate_speed if how == "left" else rotate_speed
    await motor_pair.move_tank_for_degrees(MOVE_PAIR, degrees_to_rotate, direction, -direction)
    light_matrix.clear()


async def move_arm(how: str = "down", degrees: float = 90, speed: float = 360, factor: float = 5):
    """Move the attachment arm.
    Args:
        how: "up" or "down"
        degrees: degrees to move
        speed: motor turning speed
        factor: arm-specific conversion factor.

    """
    print("Move arm {} for {} degrees with speed {} degrees/s.".format(how, degrees, speed))
    assert (how in ["up", "down"])
    degrees = int(factor * degrees)
    speed = int(speed)
    speed = -speed if how == "down" else speed
    await motor.run_for_degrees(ARM_1_MOTOR_PORT, degrees, speed)


#########################
# Advance Movement
#########################

def steering_proportion(sensor_reflection: int):
    steering = (sensor_reflection - MEDIUM_REFLECTION) * 1
    return int(steering)


def lf_stop_condition(current_time: int, current_degrees: int, color_sensor_stop: int, degrees_stop: int, time_stop: int):
    conditions = [
        # If stop time is set and time limit is reached
        time_stop >= 0 and current_time >= time_stop,
        # Or if stop distance is set and distance limit is reached
        degrees_stop >= 0 and current_degrees >= degrees_stop,
        # Or if second color sensor is set and it hits black (reflection below threshold)
        color_sensor_stop >= 0 and device.ready(color_sensor_stop) and color_sensor.reflection(color_sensor_stop) <= MEDIUM_REFLECTION,
    ]
    if any(conditions):
        print("Line following stop condition is met: ", conditions)
    return any(conditions)


async def line_follow(
    speed: float,
    color_sensor_follow: int,
    color_sensor_stop: int = -1,
    distance_stop: float = -1,
    time_stop: int = -1,
    left_motor: int = LEFT_MOTOR,
):
    """Line following with multiple options of stop conditions.

    Args:
        speed: speed cm/s
        color_sensor_follow: the port of first color sensor (int)
        color_sensor_stop: the port of second color sensor (int) for stop condition
        distance_stop: fix distance to move (cms)
        time_stop: fix time to move (seconds)
        left_motor: left motor
    """
    MAX_TIME_MS = 30000 # 30 seconds
    assert device.ready(color_sensor_follow)
    assert device.ready(left_motor)
    print("Move following line with {} color sensor: {}{}{}".format(
        color_sensor_follow,
        "" if time_stop == -1 else "stop after {} secs".format(time_stop),
        "" if distance_stop == -1 else "stop after {} cms".format(distance_stop),
        "" if color_sensor_stop == -1 else "stop if 2nd sensor hits black"
    ))
    motor.reset_relative_position(left_motor, 0)
    factor = 1.0 / (PI * WHEEL_DIAMETER) * 360
    rotate_speed = int(speed * factor)
    degrees_stop = int(factor * distance_stop) if distance_stop >= 0 else -1
    time_stop = time_stop * 1000 if time_stop >= 0 else MAX_TIME_MS
    start = time.ticks_ms()
    while time.ticks_ms() - start < time_stop:
        current_time = time.ticks_ms() - start
        current_degrees = abs(motor.relative_position(left_motor))
        steering = steering_proportion(color_sensor.reflection(color_sensor_follow))
        motor_pair.move(MOVE_PAIR, steering, velocity=rotate_speed - abs(steering))
        if lf_stop_condition(current_time, current_degrees, color_sensor_stop, degrees_stop, time_stop):
            break
    print("Stop line following.")
    motor_pair.stop(MOVE_PAIR)


#########################
# Utility functions
#########################

async def calibrate(left_motor=port.A):
    """Calibrate the conversion factor of two-wheel movement to robot turn angle.
    Args:
        left_motor: the left motor of the two wheels.

    Return: turn_factor

    """
    runloop.sleep_ms(1000)
    print("Calibrating to get the turn factor...")
    angles = motion_sensor.tilt_angles()
    motor.reset_relative_position(left_motor, 0)
    while True:
        sound.beep(440, 100, 100)
        motor_pair.move_tank(MOVE_PAIR, -80, 80)
        last = angles[0]
        angles = motion_sensor.tilt_angles()
        if last < 0:
            if angles[0] >= 0:
                motor_pair.stop(MOVE_PAIR)
                left_motor_degrees = motor.relative_position(left_motor)
                turn_factor = left_motor_degrees / 360
                return turn_factor


#########################
# Missions
#########################

async def perform_mission_1():
    await light_matrix.write("1")
    await runloop.sleep_ms(500)
    await move_arm("up", 60)
    await move("forward", 10, 40)
    await turn("left", 25, speed=20)
    await move("forward", 25, 40)
    await move_arm("down", 40)
    await turn("right", 30, speed=50)
    await move_arm("up", 60)
    await runloop.sleep_ms(500)
    await turn("left", 30)
    await move("backward", 25, 40)
    await turn("right", 30)
    await move("backward", 10)
    await move_arm("down", 60)


async def perform_mission_3_5():
    await light_matrix.write("4 & 5")
    await runloop.sleep_ms(500)
    await move_arm("up", 70)
    await move("forward", 30, 30)
    await turn("right", 90)
    await move("forward", 43, 30)
    await turn("left", 90)
    await move("forward", 43, 30)
    await move_arm("down", 70, 1220)
    await runloop.sleep_ms(500)
    await move_arm("up", 70)
    await move("backward", 20, 30)
    await move_arm("down", 70)
    await turn("right", 45)
    await move("forward", 45, 30)
    await turn("right", 180, 100)
    await move("forward", 85)
    await turn("right", 180)
    await light_matrix.write("Sleep")
    await move("forward", 40, 20)
    await turn("left", 90, 10)


async def perform_mission_7():
    await move_arm("down", 70)
    await move("forward", 55, 20)
    await move_arm("up", 35)
    await turn("right", 35)
    await move("forward", 18, 20)
    await turn("left", 15)
    await move_arm("up", 10)
    await move("backward", 15, 80)
    await turn("left", 20)
    await move("backward", 55)


async def perform_mission_8():
    await move_arm("up", 70)
    await move("forward", 68, 30)
    await turn("left", 30)
    await move("forward", 9)
    await turn("right", 75)
    await move_arm("down", 47)
    await move("forward", 11)
    await move("backward", 5)
    await move_arm("up", 5)
    await turn("left", 250, 1000)
    await move_arm("up", 60)
    await move("forward", 60, 30)
    await turn("left", 180)
    await move_arm("down", 60)


async def main():

    #await perform_mission_1()
    # await perform_mission_3_5()
    # await line_follow(speed=15, color_sensor_follow=port.B, color_sensor_stop=port.F)
    # await perform_mission_7()
    # await move_arm("up", 50, 2000)
    await perform_mission_8()


runloop.run(main())
