import numpy as np
from physics_sim import PhysicsSim

class Task():
    """Task (environment) that defines the goal and provides feedback to the agent."""
    def __init__(self, init_pose=None, init_velocities=None, 
        init_angle_velocities=None, runtime=5., target_pos=None):
        """Initialize a Task object.
        Params
        ======
            init_pose: initial position of the quadcopter in (x,y,z) dimensions and the Euler angles
            init_velocities: initial velocity of the quadcopter in (x,y,z) dimensions
            init_angle_velocities: initial radians/second for each of the three Euler angles
            runtime: time limit for each episode
            target_pos: target/goal (x,y,z) position for the agent
        """
        # Simulation
        self.sim = PhysicsSim(init_pose, init_velocities, init_angle_velocities, runtime) 
        self.action_repeat = 3
        
        # State should be all positions & velocities for 3 dimensions & 3 angles
        self.state_size = self.action_repeat * 6
        self.action_low = 0
        self.action_high = 900
        self.action_size = 4 # one for each rotor

        # Goal
        self.target_pos = target_pos if target_pos is not None else np.array([0., 0., 10.]) 

    def get_reward(self):
        """Uses current pose of sim to return reward."""
        #
        x,y,z = [0,1,2]
        curr_time = self.sim.time
        pos_z = self.sim.pose[z]
        vel_z = self.sim.v[z]
        
        # Positive/negative distance from target
        rel_dist = [ (pos - target) for pos,target in zip(self.sim.pose[:3],self.target_pos[:3])]
        # Positive distance from target
        dist = [ abs(d) for d in rel_dist ]
        
        ## Position rewards
        reward_pos_xy = 0.01 * np.tanh( 1. - sum(dist[:2]) )
        reward_pos_z = 0.05 * np.tanh( 1. - dist[z] )
        reward = reward_pos_xy + reward_pos_z
        
        # Time reward for running down the simulation clock
        reward += (curr_time - 3.0) / 5.0
        
        # Velocity reward for going towards target (@good speed)
        spread = 0.001
        time_ideal = 0.5 #how long to get to target
        v_ideal = (self.target_pos[z] - pos_z) / time_ideal
        reward_ideal = 0.01
        #
        reward += -1 * spread * (vel_z - v_ideal)**2.0 + reward_ideal
            
        return reward

    def step(self, rotor_speeds):
        """Uses action to obtain next state, reward, done."""
        reward = 0
        pose_all = []
        for _ in range(self.action_repeat):
            done = self.sim.next_timestep(rotor_speeds) # update the sim pose and velocities
            reward += self.get_reward() 
            pose_all.append(self.sim.pose)
        # Get full state
        next_state = np.concatenate(pose_all)
        return next_state, reward, done

    def reset(self):
        """Reset the sim to start a new episode."""
        self.sim.reset()
        state = np.concatenate([self.sim.pose] * self.action_repeat) 
        return state