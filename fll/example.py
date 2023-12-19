from hub import light_matrix, sound
import runloop
from hub import port, motion_sensor
import motor
import motor_pair
import device
import color


# DEFAULT PARAMETERS
# Default motor turning speed
DEFAULT_SPEED = 20 # degrees per second
PI = 3.1415926
TURN_FACTOR = 1.638
WHEEL_DIAMETER = 8.79


# Two-wheel motor setup
# Assuming ports connected: A, E
motor_pair.pair(motor_pair.PAIR_1, port.A, port.E)
MOVE_PAIR = motor_pair.PAIR_1


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
    light_matrix.write("1")
    await move_arm("up", 50)
    await move("forward", 10, 40)
    await turn("left", 25, turn_factor=TURN_FACTOR, speed=10)
    await move("forward", 25, 40)
    await turn("right", 30, turn_factor=TURN_FACTOR, speed=10)
    await runloop.sleep_ms(500)
    await turn("left", 30)
    await move("backward", 25, 40)
    await turn("right", 30)
    await move("backward", 10)
    await move_arm("down", 50)


async def perform_mission_3():
    light_matrix.write("3")
    await runloop.sleep_ms(1000)
    await move_arm("up", 70)
    await move("forward", 30, 30)
    await turn("right", 90)
    await move("forward", 44, 30)
    await turn("left", 90)
    await move("forward", 40, 30)
    await move_arm("down", 70, 720)
    await runloop.sleep_ms(500)
    await move_arm("up", 70)
    await turn("right", 180)
    await move("forward", 40, 30)
    await turn("right", 90)
    await move("forward", 44, 30)
    await turn("left", 90)
    await move("forward", 10, 30)
    await turn("left", 180)
    await move_arm("down", 70)


async def perform_mission_4_5():
    light_matrix.write("4 & 5")
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


async def main():

    await perform_mission_4_5()


runloop.run(main())
