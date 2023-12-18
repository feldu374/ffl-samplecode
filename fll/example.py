from hub import light_matrix, sound
import runloop
from hub import port, motion_sensor
import motor
import motor_pair
import device
import color
from app import music



DEFAULT_SPEED = 20 # degrees per second
PI = 3.1415926
TURN_FACTOR = 1.638
WHEEL_DIAMETER = 8.79

# Robot moving motor pair (A and E)
motor_pair.pair(motor_pair.PAIR_1, port.A, port.E)
MOVE_PAIR = motor_pair.PAIR_1

assert device.ready(port.A)
assert device.ready(port.E)
assert device.ready(port.D)

async def calibrate(left_motor=port.A):
    runloop.sleep_ms(1000)
    angles = motion_sensor.tilt_angles()
    motor.reset_relative_position(left_motor, 0)
    # print("Left position = {}".format(init_pos))
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
                print("Got turn factor = {}".format(turn_factor))
                return turn_factor


async def move(how="forward", distance=100, speed=DEFAULT_SPEED):
    """Move straight forward.
    Args:
        how: "forward" or "backward", default="forward"
        distance: move distance in cm
        speed: speed cm/s
        wheel_diameter: edge to edge diameter in cms
    """
    assert (how in ["forward", "backward"])
    factor = 1.0 / (PI * WHEEL_DIAMETER) * 360
    degrees_to_rotate = int(distance * factor)
    rotate_speed = int(speed * factor)
    print(rotate_speed)
    rotate_speed = rotate_speed if how == "forward" else -rotate_speed
    await motor_pair.move_for_degrees(MOVE_PAIR, degrees_to_rotate, 0, velocity=rotate_speed)


async def turn(how="left", degrees=90, speed=5, turn_factor=TURN_FACTOR):
    """Make a turn.
    Args:
        how: "left" or "right"
        degrees: degrees to turn
        turn_factor: factor to convert turn degrees to motor movements.
        speed: degrees per sec
    """
    assert (how in ["left", "right"])
    degrees_to_rotate = int(degrees * turn_factor)
    rotate_speed = int(speed * turn_factor * 10)
    print(turn_factor)
    direction = -rotate_speed if how == "left" else rotate_speed
    await motor_pair.move_tank_for_degrees(MOVE_PAIR, degrees_to_rotate, direction, -direction)


async def move_arm(how="down", degrees=90, speed=360, factor=4):
    """Move the attachment arm.
    Args:
        how: "up" or "down"
        degrees: degrees to move

    """
    assert (how in ["up", "down"])
    degrees = factor * degrees
    speed = -speed if how == "down" else speed
    await motor.run_for_degrees(port.D, degrees, speed)


async def perform_mission_1():
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


async def main():

    # await light_matrix.write("STARTING")
    # await move_arm("down", 40)
    # await runloop.sleep_ms(1000)
    # await move("forward", 10, 20)
    # await turn("left", 90)
    # await move("forward", 10, 20)
    # await move_arm("up", 70)
    # await move_arm("down", 70)
    # await calibrate()
    await runloop.sleep_ms(1000)
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

runloop.run(main())