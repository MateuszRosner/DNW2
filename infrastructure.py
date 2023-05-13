import configparser

class Infrastructure():
    def __init__(self, fileName):
        self.config = configparser.ConfigParser()
        self.config.read(fileName)
        
        self.infrastructure = self.config['INFRASTRUCTURE']
        self.addresses      = self.config['ADDRESSES']

        self.mainBoards     = self.addresses['MainBoard'].split(',')
        self.sensorsBoards  = self.addresses['SensorsBoard'].split(',')
        self.ambientBoards  = self.addresses['AmbientBoard'].split(',')
        self.pgmBoards      = self.addresses['PGMBoards'].split(',')

        # --------------- modules initialization ---------------
        print("INFRASTRUCTURE:")

        for key in self.infrastructure:
            print(key, (self.infrastructure[key]))

        print("\nADDRESSES:")
        for key in self.addresses:
            print(key, (self.addresses[key].split(',')))
        
        print('\n')



if __name__ == "__main__":
    inf = Infrastructure('config.ini')