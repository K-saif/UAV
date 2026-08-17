terminal 1 -  `MicroXRCEAgent udp4 -p 8888`
terminal 2 -  `cd ~/PX4-Autopilot`     ` make px4_sitl gz_x500`
terminal 3 -  `ros2 run drone_control offboard_control`
