import random

import numpy as np
from InputsConfig import InputsConfig as InputsConfig
from Models.Node import Node


class Consensus:
    global_main_chain=[] # the accpted global chain after resovling the forks


    """
	This is to model the consensus protocol
    """
    def Protocol(node):
        pass

    """
	This method is to resolve the forks that occur when nodes have multiple differeing copies of the blockchain ledger
    """
    def fork_resolution():
        pass
