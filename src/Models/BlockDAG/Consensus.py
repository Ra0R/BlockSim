import random

import numpy as np
from InputsConfig import InputsConfig as InputsConfig
from Models.Consensus import Consensus as BaseConsensus


class Consensus(BaseConsensus):
    """
    Implements leader selection functionality
    """
    current_leader = None

    """
	We modelled PoW consensus protocol by drawing the time it takes the miner to finish the PoW from an exponential distribution
        based on the invested hash power (computing power) fraction
    """
    def Protocol(miner):
        ##### Start solving a fresh PoW on top of last block appended #####
        TOTAL_HASHPOWER = sum(
            [miner.hashPower for miner in InputsConfig.NODES])
        hashPower = miner.hashPower/TOTAL_HASHPOWER
        return random.expovariate(hashPower * 1/InputsConfig.Binterval)
    
    """
    This method iterates through all blockDAg nodes and gets all the blocks
    """
    def get_global_blockDAG():

        # Start with graph of node 1
        blockDAG = InputsConfig.NODES[0].blockDAG
        
        # Get all reachable blocks
        block_ids = blockDAG.get_reachable_blocks()
        
        for block_id in block_ids:
            block = blockDAG.get_blockData_by_hash(block_id)
            
            if block != None:
                break

            if block == None:
                for node in InputsConfig.NODES:
                    if node.blockDAG.get_blockData_by_hash(block_id) != None:
                        block = node.blockDAG.get_blockData_by_hash(block_id)
            
            if block == None:
                print("Block not found")
            else:
                # Insert block into DAG
                blockDAG.add_block(block_id, block["parent"], block["references"], block["block_data"])

        return blockDAG

    """
	This method apply the longest-chain approach to resolve the forks that occur when nodes have multiple differeing copies of the blockchain ledger
    """
    def fork_resolution():
        pass
    """
        BaseConsensus.global_main_chain = []  # reset the global chain before filling it

        a = []
        for node in InputsConfig.NODES:
            a += [node.blockchain_length()]
        longest_recorded_chain = max(a)

        nodes_with_longest_chain = []
        last_node_id_with_longest_chain = 0
        for node in InputsConfig.NODES:
            if node.blockchain_length() == longest_recorded_chain:
                nodes_with_longest_chain += [node.id]
                last_node_id_with_longest_chain = node.id

        if len(nodes_with_longest_chain) > 1:
            c = []
            for node in InputsConfig.NODES:
                if node.blockchain_length() == longest_recorded_chain:
                    c += [node.last_block().miner]
            last_node_id_with_longest_chain = np.bincount(c)
            last_node_id_with_longest_chain = np.argmax(
                last_node_id_with_longest_chain)

        for node in InputsConfig.NODES:
            if node.blockchain_length() == longest_recorded_chain and node.last_block().miner == last_node_id_with_longest_chain:
                for bc in range(len(node.blockchain)):
                    BaseConsensus.global_main_chain.append(node.blockchain[bc])
                break
    """
