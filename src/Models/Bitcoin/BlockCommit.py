from InputsConfig import InputsConfig as InputsConfig
from Models.Bitcoin.Consensus import Consensus as c
from Models.Bitcoin.Node import Node
from Models.BlockCommit import BlockCommit as BaseBlockCommit
from Models.Network import Network
from Models.Transaction import FullTransaction as FT
from Models.Transaction import LightTransaction as LT
from Scheduler import Scheduler
from Statistics import Statistics


def profile(f): return f

class BlockCommit(BaseBlockCommit):

    # Handling and running Events
    @profile
    def handle_event(event):
        if event.type == "create_block":
            BlockCommit.generate_block(event)
        elif event.type == "receive_block":
            BlockCommit.receive_block(event)

    # Block Creation Event
    @profile
    def generate_block(event):
        miner = InputsConfig.NODES[event.block.miner]
        minerId = miner.id
        eventTime = event.time
        blockPrev = event.block.previous

        if blockPrev == miner.last_block().id:
            Statistics.totalBlocks += 1  # count # of total blocks created!
            if InputsConfig.hasTrans:
                if InputsConfig.Ttechnique == "Light":
                    blockTrans, blockSize = LT.execute_transactions()
                elif InputsConfig.Ttechnique == "Full":
                    blockTrans, blockSize = FT.execute_transactions(miner, eventTime)

                event.block.transactions = blockTrans
                event.block.usedgas = blockSize

            miner.blockchain.append(event.block)


            if InputsConfig.hasTrans and InputsConfig.Ttechnique == "Light":
                LT.create_transactions()  # generate transactions

            BlockCommit.propagate_block(event.block)
            # Start mining or working on the next block
            BlockCommit.generate_next_block(miner, eventTime)
            

    # Block Receiving Event
    @profile
    def receive_block(event):

        miner = InputsConfig.NODES[event.block.miner]
        minerId = miner.id
        currentTime = event.time
        blockPrev = event.block.previous  # previous block id

        node : Node = InputsConfig.NODES[event.node]  # recipint
        lastBlockId = node.last_block().id  # the id of last block

        #### case 1: the received block is built on top of the last block according to the recipient's blockchain ####
        if blockPrev == lastBlockId:
            # append the block to local blockchain
            node.blockchain.append(event.block)
            if InputsConfig.hasTrans and InputsConfig.Ttechnique == "Full":
                BlockCommit.update_transactionsPool(node, event.block)
            # Start mining or working on the next block
            BlockCommit.generate_next_block(node, currentTime)

         #### case 2: the received block is  not built on top of the last block ####
        else:
            depth = event.block.depth + 1
            if (depth > len(node.blockchain)):
                BlockCommit.update_local_blockchain(node, miner, depth)
                # Start mining or working on the next block
                BlockCommit.generate_next_block(node, currentTime)
            else:
                # if the block is not built on top of the last block, it is a forked block
                node.forkedBlocks.append(event.block)

            if InputsConfig.hasTrans and InputsConfig.Ttechnique == "Full":
                # not sure yet.
                BlockCommit.update_transactionsPool(node, event.block)

    # Upon generating or receiving a block, the miner start working on the next block as in POW
    def generate_next_block(node, currentTime):
        if node.hashPower > 0:
            # time when miner x generate the next block
            blockTime = currentTime + c.Protocol(node)
            Scheduler.create_block_event(node, blockTime)

    def generate_initial_events():
        currentTime = 0
        for node in InputsConfig.NODES:
            BlockCommit.generate_next_block(node, currentTime)

    def propagate_block(block):
        for recipient in InputsConfig.NODES:
            if recipient.id != block.miner:
                # draw block propagation delay from a distribution !! or you can assign 0 to ignore block propagation delay
                blockDelay = Network.block_prop_delay()
                Scheduler.receive_block_event(recipient, block, blockDelay)
