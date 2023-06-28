import itertools


class ParameterSpace:
    blocks_per_second = [0.5, 1, 13, 300, 600]
    tx_delay = [0, 1, 5, 10, 15.1]
    block_delay = [tx_delay[0], tx_delay[1], tx_delay[2],
                   tx_delay[3], tx_delay[4]]  # In relation to tx_delay
    tx_per_second = [1, 10, 60]  # TODO: multiples of block_size

    combinations = list(itertools.product(blocks_per_second, tx_delay, block_delay, tx_per_second))

    def __init__(self):
        pass

    def get_combination(self):
        return self.combinations.pop()

    def get_combination(self, index):
        return self.combinations[index]
