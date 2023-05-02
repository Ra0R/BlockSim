import random

from Event import Event, Queue
from InputsConfig import InputsConfig
from Models.BlockDAG.Block import Block


class BlockDAGScheduler:

    # Schedule a block creation event for a miner and add it to the event list
    def create_block_event(miner, eventTime):
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
            if(len(miner.forkedBlocks) > 0):
                block.references = []
                for forkedBlock in miner.forkedBlocks:
                    if not miner.blockDAG.block_exists(forkedBlock.id):
                        block.references.append(forkedBlock.id)

            event = Event(eventType, block.miner, eventTime,
                          block)  # create the event
            Queue.add_event(event)  # add the event to the queue
