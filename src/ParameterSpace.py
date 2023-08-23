import itertools


class ParameterSpace:
    block_creation_interval = [0.5, 1, 2, 50, 600]
    tx_delay = [0.150, 2, 5, 10, 15, 30]
    # Defines the block delay multiplier in regards to transaction delay
    block_delay_multiplier = [1, 2, 3, 4, 5]
    combinations = list(itertools.product(block_creation_interval, tx_delay, block_delay_multiplier))

    def __init__(self):
        pass

    def get_combination(self):
        return self.combinations.pop()

    def get_combination(self, index) :
        # return combination and append block delay
        return self.combinations[index]
