# Sample code for FLL Spike Prime python version 2023

<image src="https://blog.tcea.org/wp-content/uploads/2022/12/Screen-Shot-2022-12-02-at-10.20.09-AM.png" width="200px">

Simple codes for 2023 FLL MASTERPIECE challenges written in Python.

## Introduction

Some useful library methods with a simple attachment can help to complete several missions
```python

async def move(how: str = "forward", distance: float = 100, speed: float = 20):
    ...

async def turn(how: str = "left", degrees: float = 90, speed: float = 10, turn_factor: float = TURN_FACTOR):
    ...

async def move_arm(how: str = "down", degrees: float = 90, speed: float = 360, factor: float = 5):
    ...

```

