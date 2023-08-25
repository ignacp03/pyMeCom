import numpy as np
import matplotlib.pyplot as plt

def sin_square_with_plateau(ramp_time, high_time, high_power, sampling_time, generate_csvfile= False):
    high_points = high_time//sampling_time
    ramp_points = ramp_time//sampling_time
    ramp_angles = np.linspace(0,np.pi/2, int(ramp_points))
    ramp_up = high_power * np.sin(ramp_angles)**2
    ramp_down = high_power * np.sin(ramp_angles+np.pi/2)**2
    high = np.ones(int(high_points))*high_power
    sequence = np.concatenate((ramp_up,high,ramp_down))
    plt.plot(np.arange(0,len(sequence))/100,sequence)
    plt.xlabel('Time (ms)')
    plt.ylabel('Power(W)')
    plt.show()

    if generate_csvfile:
        sequence = sequence.reshape(-1, 1)
        first_column = ['']*len(sequence)
        f = open("sin_square_with_plateau.csv", "w")
        f.write('Table Instance ; 1\n')
        for i in range(len(sequence)):
            f.write(first_column[i]+'; '+str(sequence[i][0])+'\n')
        f.close()

def general_sigmoid_offset(offset_time, ramp_time, high_time, high_power, sampling_time, generate_csvfile = False):
    """"
    All times in us
    """
    
    high_points = high_time//sampling_time
    ramp_points = ramp_time//sampling_time
    offset_points = offset_time//sampling_time
    ramp_angles = np.linspace(0,np.pi/2, int(ramp_points))
    ramp_up = high_power * np.sin(ramp_angles)**2
    ramp_down = high_power * np.sin(ramp_angles+np.pi/2)**2
    high = np.ones(int(high_points))*high_power
    offset = np.zeros(int(high_points))*high_power
    sequence = np.concatenate((offset,ramp_up,high,ramp_down, offset))
    x = np.arange(0,len(sequence))*sampling_time
    plt.plot(x/1000,sequence)
    plt.xlabel('Time (ms)')
    plt.ylabel('Power(W)')
    plt.show()
    if generate_csvfile:
        sequence = sequence.reshape(-1, 1)
        first_column = ['']*len(sequence)
        f = open("general_sigmoid_offset.csv", "w")
        f.write('Table Instance ; 1\n')
        for i in range(len(sequence)):
            f.write(first_column[i]+'; '+str(sequence[i][0])+'\n')
        f.close()