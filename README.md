# UAV

## 🚁 Overall roadmap

```text
PHASE 1
Understand simulation + single drone
        ↓
Follow-me drone
        ↓
Obstacle avoidance
        ↓
Basic autonomy

PHASE 2
Fully autonomous single drone
        ↓
A → B navigation
        ↓
Perception + localization
        ↓
Exploration
        ↓
Mission planning
        ↓
Return-to-home / failsafes

PHASE 3
Multi-drone / swarm
        ↓
Drone ↔ Drone communication
        ↓
Task allocation
        ↓
Cooperative exploration
        ↓
Shared map
        ↓
Decentralized swarm
```

### Phase 1 — Learn the drone

Your first objective shouldn't even be "AI."

Understand:

* What PX4 actually does
* What the simulator does
* How physics are simulated
* What ROS 2 does
* How ROS 2 communicates with PX4
* Sensors
* IMU
* GPS
* Camera
* Altitude
* Position / velocity / attitude
* MAVLink / DDS
* Offboard control

Then make your first drone do simple things:

```text
Takeoff
   ↓
Hover
   ↓
Move forward
   ↓
Move left/right
   ↓
Change altitude
   ↓
Return
   ↓
Land
```

Then:

### Phase 1A

**Follow-me**

```text
Person
  ↓
Camera
  ↓
Person detection
  ↓
Person position
  ↓
Target position
  ↓
PX4 / ROS 2
  ↓
Drone follows
```

Then improve it:

* maintain distance
* maintain altitude
* smoother movement
* lose-target handling
* obstacle avoidance
* reacquire target
* emergency landing

That alone becomes a substantial project.

---

# Phase 2 — Remove the human

This is where the project changes character.

Instead of:

```text
Human
 ↓
Target
 ↓
Drone follows
```

you say:

```text
Mission:
Go from A → B
```

The drone figures out how to get there.

Start extremely simple:

```text
A ───────────────────────→ B
```

Then introduce obstacles:

```text
A ────────┐
          │
       obstacle
          │
          └────────────── B
```

Drone needs to:

1. detect obstacle
2. plan around it
3. continue toward B
4. reach B
5. report completion

Then add:

**Return to home**

```text
A → B → A
```

Then:

**Multiple waypoints**

```text
A → B → C → D → A
```

Then:

**Exploration**

```text
         ┌─────────────┐
         │             │
         │  unexplored │
         │             │
         │      B      │
         │             │
         └─────────────┘
```

Instead of being given B, the drone decides where B should be.

That's the transition from **autonomous navigation → autonomous exploration**.

---

# Phase 3 — Swarm

Only after Phase 2 is working well should you introduce the second drone.

Start ridiculously simple:

```text
Drone 1                 Drone 2
   ↓                       ↓
Takeoff                  Takeoff
   ↓                       ↓
Fly                      Fly
   ↓                       ↓
Land                     Land
```

Then:

### Communication

```text
Drone 1 ←────────→ Drone 2
```

Share:

* position
* velocity
* battery
* state
* target

Then:

### Collision avoidance

Make them capable of flying independently without crashing into each other.

Then:

### Cooperative navigation

```text
              Target area

       ┌────────────────────┐
       │                    │
       │ D1 →               │
       │                    │
       │             ← D2   │
       │                    │
       └────────────────────┘
```

Then:

### Cooperative exploration

```text
                Area
       ┌─────────────────────┐
       │       D1            │
       │                     │
       │                     │
       │                     │
       │              D2     │
       └─────────────────────┘

          ↕ communication ↕
```

Eventually:

> **The drones decide among themselves who explores what.**

That's the final vision you described.

---

## One important architectural decision

Since you want this to eventually become a swarm, **build your software architecture from Phase 1 as if there could eventually be multiple drones.**

For example, don't hard-code everything as:

```text
/drone
```

Prefer:

```text
/drone1/pose
/drone1/state
/drone1/camera

/drone2/pose
/drone2/state
/drone2/camera
```

Even when you only have one drone.

Your autonomy layer can eventually become:

```text
                Swarm Manager
                     │
          ┌──────────┴──────────┐
          ↓                     ↓
     Drone Agent 1         Drone Agent 2
          ↓                     ↓
        PX4                   PX4
```


---
