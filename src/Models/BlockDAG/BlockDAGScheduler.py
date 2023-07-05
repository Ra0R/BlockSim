import random

from Event import Event, Queue
from InputsConfig import InputsConfig
from Models.BlockDAG.Block import Block
from Models.BlockDAG.Node import Node


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


            # Extend forked blocks
            if(len(miner.forkedBlockCandidates) > 0):
                references = []
                included_blocks = []
                for forkedBlock in miner.forkedBlockCandidates:
                    
                    if not miner.blockDAG.is_in_chain_of_block(block.previous, forkedBlock.id):
                        print("Block " + str(forkedBlock.id) +  " is not in the chain of block " + str(block.previous))
                        references.append(forkedBlock.id)
                        included_blocks.append(forkedBlock)

            
                # Check if after adding a reference, the block is in the chain of another reference
                for ref1 in references:
                    graph_sim = miner.blockDAG.simluate_add_block(block.id, block.previous, [ref1])
                    for ref2 in references:
                        if not ref1 == ref2:
                            if miner.blockDAG.is_in_chain_of_block(ref1, ref2, graph_sim):
                                print("Referenced block: " + str(ref1) +  " is already in the chain of another reference: " + str(ref2))
                                if ref1 in references:
                                    references.remove(ref1)

                            if miner.blockDAG.is_in_chain_of_block(ref2, ref1, graph_sim):
                                print("Referenced block: " + str(ref2) +  " is already in the chain of another reference: " + str(ref1))
                                if ref2 in references:
                                    references.remove(ref2)

                block.references = references
                
            event = Event(eventType, block.miner, eventTime,
                          block)  # create the event
            Queue.add_event(event)  # add the event to the queue