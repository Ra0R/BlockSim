import itertools


class ParameterSpace:
    block_creation_interval = [0.5, 1, 2, 50, 600]
    tx_delay = [0.150, 2, 5, 10, 15]
    
    combinations = list(itertools.product(block_creation_interval, tx_delay))
    
    def __init__(self):
        pass

    def get_combination(self):
        return self.combinations.pop()

    def get_combination(self, index) :
        # return combination and append block delay
        return self.combinations[index]
