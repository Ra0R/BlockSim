import random as r_block
import random as r_tx

from InputsConfig import InputsConfig as InputsConfig

if InputsConfig.seed_creation:
    r_block.seed(InputsConfig.seed)


#random.seed(InputsConfig.seed)

class Network:

    # Delay for propagating blocks in the network
    def block_prop_delay():
        return r_block.expovariate(1/InputsConfig.Bdelay)

    # Delay for propagating transactions in the network
    def tx_prop_delay():
        return r_tx.expovariate(1/InputsConfig.Tdelay)
