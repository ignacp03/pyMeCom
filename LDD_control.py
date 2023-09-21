"""
control example
"""

import logging
from mecom import MeCom, ResponseException, WrongChecksum, LT_download_manager
from serial import SerialException
import warnings
import numpy as np
import matplotlib.pyplot as plt


# default queries from command table below
DEFAULT_QUERIES = [
    "Device_status"
    "current",
    "max current",
]

# syntax
# { display_name: [parameter_id, unit], }
COMMAND_TABLE = {
    "Device Status": [104, ""],
    "current": [1016, "A"],
    "max current": [3020, "A"]
}

class BlueLDD(object):
    """
    Controlling Laser diode devices via serial.
    """

    def _tearDown(self):
        self.session().stop()

    def __init__(self, port="COM6", channel=1, queries=DEFAULT_QUERIES, *args, **kwars):
        assert channel in (1, 2)
        self.channel = channel
        self.port = port
        self.queries = queries
        self._session = None
        self._connect()

    def _connect(self):
        # open session
        self._session = MeCom(serialport=self.port,metype = 'LDD')
        # get device address
        self.address = self._session.identify()
        logging.info("connected to {}".format(self.address))

    def session(self):
        if self._session is None:
            self._connect()
        return self._session

    def get_data(self):
        data = {}
        for description in self.queries:
            id, unit = COMMAND_TABLE[description]
            try:
                value = self.session().get_parameter(parameter_id=id, address=self.address, parameter_instance=self.channel)
                data.update({description: (value, unit)})
            except (ResponseException, WrongChecksum) as ex:
                self.session().stop()
                self._session = None
        return data
    
    def single_sequence(self, get = False, set = None ):
        """
        Allows to trigger a single sequence by a analog logic input. For this to work 
        PBC RES4 must be set to: Single sequence in the settings tab of the sequence or command 3080
        must be send to the instance 4 with the value 10. 

        If get is set to true, the function returns the current state.
        If option is set to 0 (1), it sets OFF (ON).
        """
        if get:
            value = self.session().get_parameter(parameter_id=2009, address=self.address, parameter_instance=self.channel)
            if value == 1: print('Single sequence is currently ON')
            if value == 0: print('Single sequence is currently OFF')
        if set is not None:
            sent = self.session().set_parameter(value=set, parameter_id=2009, address=self.address, parameter_instance=self.channel)
            if set == 1: print('Single sequence set to ON:', sent)
            if set == 0: print('Single sequence set to OFF:', sent)

    def set_current_input_source(self, option:int):
        """
        Select between the input sources:
        0: Internal generator
        1: CW
        2: Data Interfaces
        3: HW Pin
        4: LPC 
        5: Look up Table
        """
        assert type(option) is int and option >= 0 and option <= 5, "only int 0,...,5 allowed"
        options = ['Internal generator', 'CW', 'Data Interfaces', 'HW Pin', 'Laser Power Control', 'Look up Table']
        response = self.session().set_parameter(value=option, parameter_id=2000, address=self.address, parameter_instance=self.channel)
        if response == True:
            print('The current input source was set to: '+options[option])
        else:
            print('There was an eror sending the command')
    
    def download_lookup_table(self, file):
        """
        Downloads lookup table
        file: path (str)
        table_instances: list 
        """
        DM = LT_download_manager(file, self.session())
        download = DM.download_table()
        
        return DM
    
    def set_power_input_source(self, option:int):
        """
        Select between the input sources:
        0: Internal generator
        1: CW
        2: Data Interfaces
        3: Look up Table
        """
        assert type(option) is int and option >= 0 and option <= 3, "only int 0,...,5 allowed"
        options = ['Internal generator', 'CW', 'Data Interfaces (Ramp mode)', 'HW Pin', 'LPC', 'Look up Table']
        response = self.session().set_parameter(value=option, parameter_id=5000, address=self.address, parameter_instance=self.channel) 
        if response == True:
            print('Power input set to: '+options[option])
        else:
            print('There was an error sending the command')
    
    def set_LP_CW(self, value):
        """
        Set power value in CW mode
        value: float
        """
        assert type(value) is float, "value must be a float type"
        logging("Set power in CW mode to {} W".format(self.channel, value))
        return self.session().set_parameter(value=value, parameter_id=5001, address=self.address, parameter_instance=self.channel)
    
    def set_LP_signal(self, high_power,high_time, rise_time, fall_time = None, low_power = 0, low_time = 1e-6 ):
        """
        High power: float. Max power (0...1000 W)
        Low power: float. Min power (0...1000 W)
        high time: float. Time at max power (1e-6...10 s)
        low time: float. Time at min power (1e-6...10 s)
        rise time: float. Time between min and max power (1e-6...10 s)
        fall time: float. Time between max and min power(1e-6...10 s)
        """
        if fall_time == None:
            fall_time = rise_time

        params = [high_power,low_power, high_time, low_time, rise_time, fall_time]
        commands = ['High Power', 'Low Power', 'High Time', 'Low Time', 'Rise Time', 'Fall Time']
        params_units = ['W','W', 's', 's','s','s']
        response = []
        for i in range(6):
            id= 5002 + i
            response.append(self.session().set_parameter(value=params[i], parameter_id=id, address=self.address, parameter_instance=self.channel))

        if all(response) == True:
            print('Ramp pulse parameters succesfully loaded')
        else:
            for i in range(len(response)):
                if response[i] != True: print('There was an error loading: '+commands[i])


    def set_PID_LPC_params(self, Kp = None, Ki=None, Kd = None, slope_lim= None):
        """
        Kp: float. (1E-3...1000 A/W)
        Ki: float. (1E-6...10 s)
        high time: float.  (0...10 s)
        low time: float. (1E-6...1 W/us)
        """
        params = [Kp, Ki, Kd, slope_lim]
        params_name = ['Kp','Ki', 'Kd', 'slope limit']
        params_units = ['A/W', 's', 's', 'W/us']
        for i in range(4):
            if params[i] != None:
                logging.info("Set "+params_name[i]+"  to "+str(params[i])+" " +params_units[i])
                id= 5010 + i
                self.session().set_parameter(value=params[i], parameter_id=id, address=self.address, parameter_instance=self.channel)

    def get_PD_current(self):
        """
        Returns photodiode current, must be < 1mA
        """
        value = self.session().get_parameter(parameter_id=1060, address=self.address, parameter_instance=self.channel)
        print(value, ' A')
        if value > 0.001 : warnings.warn('Photocurrent larger than thresold (1 mA), reduce it!!') 
        return value

    
    def set_current(self, value):
        """
        Set laser diode cw current
        :param value: float
        :param channel: int
        :return:
        """
        # assertion to explicitly enter floats
        assert type(value) is float
        logging.info("set current to {} C".format(self.channel, value))
        return self.session().set_parameter(parameter_id=2001, value=value, address=self.address, parameter_instance=self.channel)

    def set_lookup_table_setings(self, Interval = None, selection = None):
        """
        Interval: int. (0 ... 1e7us)
        selection: int. Number of the 4 possible tables (0...3)
        """
        params = [Interval, selection]
        params_name = ['Interval', 'Table']
        params_units = ['us', '']
        for i in range(2):
            if params[i] != None:
                logging.info("Set "+params_name[i]+"  to "+str(params[i])+" " +params_units[i])
                id= 4200 + 10*i
                self.session().set_parameter(value=params[i], parameter_id=id, address=self.address, parameter_instance=self.channel)

    def set_current_limit(self, value):
        """
        Set laser diode cw current limit
        :param value: float
        :param channel: int
        :return:
        """
        # assertion to explicitly enter floats
        assert type(value) is float
        logging.info("set current limit to {} C".format(self.channel, value))
        return self.session().set_parameter(parameter_id=3020, value=value, address=self.address, parameter_instance=self.channel)

    def _set_enable(self, enable=True):
        """
        Enable or disable control loop
        :parlam enable: bool
        :param channel: int
        :return:
        """
        value, description = (1, "on") if enable else (0, "off")
        logging.info("set current output to {} to {}".format(self.channel, description))
        return self.session().set_parameter(value=value, parameter_id=2020, address=self.address, parameter_instance=self.channel)

    def enable(self):
        return self._set_enable(True)

    def disable(self):
        return self._set_enable(False)
    
    def send_other_command(self, id, function, value = None):
        """
        Allows sending commands not specified above.
        Id: command ID. Use the MeCom documentation to find the command Id.
        function: 0: get, 1: set.
        value: value to set. Check the documentation to send it in the propper format.
        """
        if function == 0:
            value = self.session().get_parameter(parameter_id=id, address=self.address, parameter_instance=self.channel)
            return value
        elif function ==1:
            return self.session().set_parameter(parameter_id=id, value = value, address=self.address, parameter_instance=self.channel)


