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
                block.references = []
                included_blocks = []
                for forkedBlock in miner.forkedBlockCandidates:
                    if not miner.blockDAG.is_in_chain_of_block(block.previous, forkedBlock.id):
                        block.references.append(forkedBlock.id)
                        included_blocks.append(forkedBlock)
                    else:
                        print("Block " + str(forkedBlock.id) +  " is already in the chain of block " + str(block.previous))
                        
                # Remove included blocks from forked blocks
                # for included_block in included_blocks:
                #   miner.forkedBlockCandidates.remove(included_block)

            event = Event(eventType, block.miner, eventTime,
                          block)  # create the event
            Queue.add_event(event)  # add the event to the queue
