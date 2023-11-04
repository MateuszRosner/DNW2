

class Resources():
    def __init__(self):
        self.output_ports = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.output_currs = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.liquids      = [0, 0, 0, 0, 0]
        self.temperature  = [223, 234, 0]
        self.pressure     = [0, 0, 0]
        self.humidity     = [234, 332, 0]
        self.gas          = [0, 0, 0]
        self.total_curr   = 0.0
        self.relays       = 0x03FF
        self.ac_state     = False
        self.temp_on      = False
        self.ac_temp      = 22
        self.anti_freez   = False
        self.tempdate     = 0