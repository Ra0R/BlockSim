from InputsConfig import InputsConfig as InputsConfig
from Models.BlockCommit import BlockCommit as BaseBlockCommit
from Models.BlockDAG.BlockDAGraph import BlockDAGraphComparison
from Models.BlockDAG.BlockDAGScheduler import BlockDAGScheduler
from Models.BlockDAG.Consensus import Consensus as c
from Models.BlockDAG.Node import Node
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
        elif event.type == "extend_block":
            BlockCommit.extend_block(event)

    # Block Creation Event
    def generate_block(event):
        miner : Node = InputsConfig.NODES[event.block.miner]
        minerId = miner.id
        eventTime = event.time
        blockPrev = event.block.previous

        if blockPrev == miner.last_block():
            Statistics.totalBlocks += 1  # count # of total blocks created!
            if InputsConfig.hasTrans:
                if InputsConfig.Ttechnique == "Light":
                    blockTrans, blockSize = LT.execute_transactions()
                elif InputsConfig.Ttechnique == "Full":
                    blockTrans, blockSize = FT.execute_transactions(
                        miner, eventTime)

                event.block.transactions = blockTrans
                event.block.usedgas = blockSize
            if len(miner.forkedBlocks) > 0:
                BlockCommit.acknowledge_blocks(miner, eventTime, miner.forkedBlocks, event.block)            


            miner.blockDAG.add_block(event.block.id, event.block.previous, [], event.block)
            
            BlockCommit.propagate_block(event.block)
            # Start mining or working on the next block
            BlockCommit.generate_next_block(miner, eventTime)

    def acknowledge_blocks(miner : Node, eventTime, forkedBlocks, block):
        forkedBlocks = miner.forkedBlocks
        
        miner.forkedBlocks = []

        references = [block.previous for block in forkedBlocks]
        miner.blockDAG.add_block(block.id, block.previous, references, block)
            
        BlockCommit.propagate_block(block)
        BlockCommit.generate_next_block(miner, eventTime)
        
    # Block Receiving Event
    def receive_block(event):

        miner = InputsConfig.NODES[event.block.miner]
        minerId = miner.id
        currentTime = event.time
        blockPrev = event.block.previous  # previous block id

        node: Node = InputsConfig.NODES[event.node]  # recipint
        lastBlockId = node.last_block()  # the id of last block

        # > case 1: the received block is built on top of the last block according to the recipient's blockchain ####
        if blockPrev == lastBlockId:
            # append the block to local blockchain
            # node.blockchain.append(event.block)

            references = [] if not hasattr(event.block, 'references') else event.block.references
            node.blockDAG.add_block(event.block.id, event.block.previous, references, event.block)

            BlockCommit.update_transactionsPool(node, event.block)

            # remove block from forkedBlocks blockchain if it is there
            # TODO: Also remove from mempool
            for included_block_id in references:
                BlockCommit.remove_included_block_from_forks(node, included_block_id)

            # Start mining or working on the next block
            BlockCommit.generate_next_block(node, currentTime)

         # > case 2: the received block is  not built on top of the last block --> either we need to sync the state of the chain to that block
         # or it is a forked block if we are already passed that
        else:
            
            depth = event.block.depth + 1 # Why +1?

            # We are behind, sync the state
            if (depth > node.blockDAG.get_depth()):
                BlockCommit.update_local_blockchain(node, miner, depth)
                # Start mining or working on the next block
                BlockCommit.generate_next_block(node, currentTime)

            # Block arrives at the same depth as the current block    
            elif (depth == node.blockDAG.get_depth()):                
                # 1) it is a forked block
                node.forkedBlocks.append(event.block)

                # 2) the current head will be forked
                node.forkedBlocks.append(node.blockDAG.get_blockData_by_hash(node.last_block()))

                BlockCommit.update_transactionsPool(node, event.block)

                print(node)
            else: #TODO: I think: It is a forked block and we are already passed that
                print("What is happening here?")
                # # if the block is not built on top of the last block, it is a forked block
                node.forkedBlocks.append(event.block)

                # # TODO: Should this be done in block generation instead?
                BlockCommit.update_transactionsPool(node, event.block)
                
    # Upon generating or receiving a block, the miner start working on the next block as in POW
    def generate_next_block(node, currentTime):
        if node.hashPower > 0:
            # time when miner x generate the next block
            blockTime = currentTime + c.Protocol(node)
            BlockDAGScheduler.create_block_event(node, blockTime)
            # Scheduler.create_block_event(node, blockTime)

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

    # Update local blockchain, if necessary, upon receiving a new valid block
    def update_local_blockchain(node, miner, depth):
        """
        This function updates the local blockchain of the node upon receiving a new valid block
        :param node: the node that receives the new block
        :param miner: the miner who generated the new block
        :param depth: the depth of the new block

        - Remove transactions from the mempool pool that are included in the new block
        - Exclude blocks referenced by the new block from the forkedBlocks blockchain
        - Copy chain from miner to node
        
        Example:
        node.blockchain = [1,2,3,4,5,6,7,8,9,10]
        len(blockchain) = 10
        miner.blockchain = [1,2,3,4,5,6,7,8,9,10,11,12,13,14]
        depth = 11 # I guess depth can be lower than the length of the miner's blockchain?
        
        node.blockchain = [1,2,3,4,5,6,7,8,9,10,11]

        # TODO: Maybe extract deliver block into seperate function
        """

        # the node here is the one that needs to update its blockchain, while miner here is the one who owns the last block generated
        # the node will update its blockchain to mach the miner's blockchain

        # for i in range(len(node.blockchain), max( len(node.blockchain), depth)):
        # This doesn't really work to sync a blockDAG to sync we need:
        # 1. check if the block is in the blockDAG
        # 2. if it is, check if it is in the right order
        if node.blockDAG.get_depth() < miner.blockDAG.get_depth(): # TODO: This is only heuristic, we need to check if the block is in the right order
            missing_blocks = BlockDAGraphComparison.get_differing_blocks(node.blockDAG, miner.blockDAG)

            # TODO: A bit hacky, but it works also check:
            # BlockDAGGraph.get_depth_of_block(block_id)

            # Order missing blocks by depth, otherwise we might try to add a block that references a block that hasn't been added yet
            missing_blocks = sorted(missing_blocks, key=lambda block: max(
                node.blockDAG.get_depth_of_block(block), miner.blockDAG.get_depth_of_block(block)))
            
            for block_id in missing_blocks:
                # remove transactions from the mempool pool that are included in the new block
                block_data = miner.blockDAG.get_blockData_by_hash(block_id)

                BlockCommit.update_transactionsPool(node, block_data)
                references = [] if not hasattr(block_data, 'references') else block_data.references

                # exclude blocks referenced by the new block from the forkedBlocks blockchain
                BlockCommit.exclude_referenced_blocks_from_forkedBlocks_and_mempool(node, references)

                node.blockDAG.add_block(block_id, block_data.previous, references, block_data)

    # TODO: Move to node class
    def remove_included_block_from_forks(node, block_id):
        for block in node.forkedBlocks:
            if block.id == block_id:
                node.forkedBlocks.remove(block)
                break

    def exclude_referenced_blocks_from_forkedBlocks_and_mempool(node, references):
        for blockId in references:
            BlockCommit.remove_included_block_from_forks(node, blockId)

            # Remove transactions from the mempool pool that are included in the new block
            blockData = node.blockDAG.get_blockData_by_hash(blockId) 
            # TODO: Not sure the block might not be in the blockDAG,
            #  but the transactions might still be in the mempool
            if blockData is not None:
                BlockCommit.update_transactionsPool(node, blockData)