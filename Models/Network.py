import random

from InputsConfig import InputsConfig as InputsConfig


class Network:

    # Delay for propagating blocks in the network
    def block_prop_delay():
        return random.expovariate(1/InputsConfig.Bdelay)

    # Delay for propagating transactions in the network
    def tx_prop_delay():
        return random.expovariate(1/InputsConfig.Tdelay)
