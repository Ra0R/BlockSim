import itertools


class ParameterSpace:
    block_creation_per_second = [0.5, 1, 2, 50, 600]
    tx_delay = [0.150, 2, 5, 10, 15]
    block_delay = [tx_delay[0]*2, tx_delay[1]*2, tx_delay[2]*2, tx_delay[3]*1.5, tx_delay[4]]  # In relation to tx_delay

    combinations = list(itertools.product(block_creation_per_second, tx_delay, block_delay))
    
    def __init__(self):
        pass

    def get_combination(self):
        return self.combinations.pop()

    def get_combination(self, index) :
        return self.combinations[index]
