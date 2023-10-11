import itertools

class ParameterSpace:
    #block_creation_interval = [0.5, 1, 2, 50, 600]
    block_creation_interval = [0.5, .75, 1, 2, 3, 5, 10]
    #tx_delay = [0.150, 2, 5, 10, 15, 30]
    tx_delay = [0.5, 5, 10 , 15, 30, 60]
    # Defines the block delay -> this may produce some non-sensical combinations
    # where block_delay < tx_delay, but this is not a problem
    block_delay = [5]
    
    combinations = list(itertools.product(block_creation_interval, tx_delay, block_delay))

    def __init__(self):
        pass

    def get_combination(self, index) :
        # return combination and append block delay
        return self.combinations[index]
