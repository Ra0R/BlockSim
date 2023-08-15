import random

from Event import Event, Queue
from InputsConfig import InputsConfig
from Models.BlockDAG.Block import Block
from Models.BlockDAG.Node import Node

random.seed(InputsConfig.seed)

class BlockDAGScheduler:

    # Schedule a block creation event for a miner and add it to the event list
    def create_block_event(miner : Node, eventTime):
        eventType = "create_block"
        if eventTime <= InputsConfig.simTime:
            # prepare attributes for the event
            block = Block()
            block.miner = miner.id
            block.depth = miner.blockDAG.get_depth() #TODO: Is this correct? How is depth used
            block.id = random.randrange(100000000000) 
            block.previous = miner.last_block()
            block.timestamp = eventTime
            print("------CREATING BLOCK " + str(block.id) + "------")

            # Extend forked blocks
            if(len(miner.forkedBlockCandidates) > 0):
                references = []
                included_blocks = []
                for forkedBlock in miner.forkedBlockCandidates:
                    if not miner.blockDAG.block_exists(forkedBlock.id):
                        continue
                    
                    if miner.blockDAG.is_referenced(forkedBlock.id):
                       continue

                    # Check if forkedBlock contains any transaction that is not already included in the chain
                    includeable_tx = False
                    for tx in forkedBlock.transactions:
                        if not miner.blockDAG.contains_tx(tx):
                            includeable_tx = True
                            break
                        
                    if not includeable_tx:
                        continue

                    if not miner.blockDAG.is_in_chain_of_block(block.previous, forkedBlock.id):
                        print("Block " + str(forkedBlock.id) +  " is not in the chain of block " + str(block.previous))
                        references.append(forkedBlock.id)
                        included_blocks.append(forkedBlock)


                ref_copy = references.copy()

                # Check if after adding a reference, the block is in the chain of another reference
                for ref1 in references:
                    graph_sim = miner.blockDAG.simluate_add_block(block.id, block.previous, [ref1])
                    for ref2 in references:    
                        if not ref1 == ref2:
                            if miner.blockDAG.is_referenced(ref2, graph_sim):
                                if ref2 in ref_copy:
                                        ref_copy.remove(ref2)
                                        continue

                            if miner.blockDAG.is_in_chain_of_block(ref1, ref2, graph_sim):
                                print("Referenced block: " + str(ref2) +  " is already in the chain of another reference: " + str(ref1))
                                if ref2 in ref_copy:
                                    ref_copy.remove(ref2)

                            if miner.blockDAG.is_in_chain_of_block(ref2, ref1, graph_sim):
                                print("Referenced block: " + str(ref1) +
                                      " is already in the chain of another reference: " + str(ref2))
                                if ref1 in ref_copy:
                                    ref_copy.remove(ref1)

                block.references = ref_copy
                
            event = Event(eventType, block.miner, eventTime,
                          block)  # create the event
            Queue.add_event(event)  # add the event to the queue