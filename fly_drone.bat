@echo off
echo =======================================================
echo     INITIATING AUTONOMOUS GESTURE DRONE FLIGHT SUITE   
echo =======================================================

echo [1/5] Resetting and Attaching Laptop Webcam...
usbipd detach --busid 2-1 >nul 2>&1
timeout /t 1 >nul
usbipd attach --wsl --busid 2-1

echo [2/5] Launching Gazebo Simulation (Terminal 1)...
start "Terminal 1: Gazebo Sim" cmd /k wsl.exe -d Ubuntu-24.04 -- bash -c "cd ~/PX4-Autopilot && make px4_sitl gz_x500"

echo Waiting for Gazebo matrix to initialize...
timeout /t 8

echo [3/5] Starting XRCE-DDS Communications Bridge (Terminal 2)...
start "Terminal 2: DDS Bridge" cmd /k wsl.exe -d Ubuntu-24.04 -- bash -c "MicroXRCEAgent udp4 -p 8888"

timeout /t 3

echo [4/5] Activating ROS 2 Gesture Controller Node (Terminal 3)...
start "Terminal 3: Flight Core" cmd /k wsl.exe -d Ubuntu-24.04 -- bash -c "source /opt/ros/jazzy/setup.bash && source ~/colcon_ws/install/setup.bash && ros2 run px4_control square_mission"

timeout /t 2

echo [5/5] Initializing MediaPipe Computer Vision Camera (Terminal 4)...
start "Terminal 4: Camera vision" cmd /k wsl.exe -d Ubuntu-24.04 -- bash -c "source /opt/ros/jazzy/setup.bash && source ~/colcon_ws/install/setup.bash && sudo chmod 666 /dev/video* && ros2 run px4_control gesture_camera"

echo =======================================================
echo   ALL SYSTEMS ONLINE. HAPPY FLYING!
echo =======================================================
pause
