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
                    blockTrans, blockSize = FT.execute_transactions(miner, eventTime)

                event.block.transactions = blockTrans
                event.block.usedgas = blockSize
            # event.block_rx_timestamp[minerId] = eventTime
            # event.block.rx_timestamp = eventTime
            
            # Add immediately to local node's blockDAG
            miner.blockDAG.add_block(event.block.id, event.block.previous, event.block.references, event.block)
            
            # Block may become forked
            miner.forkedBlockCandidates += [event.block]

            # Remove transactions from mempool
            BlockCommit.update_transactionsPool(miner, event.block, eventTime)
            # Remove references from mempool 
            BlockCommit.exclude_referenced_blocks_from_forkedBlocks_and_mempool(miner, event.block.references, eventTime)

            BlockCommit.propagate_block(event.block)
            # Start mining or working on the next block
            BlockCommit.generate_next_block(miner, eventTime)
        else:
            print("Block " + str(event.block.id) + " is not built on top of the last block " + str(blockPrev) + " of node " + str(minerId) + " at time " + str(eventTime) + " but on top of " + str(miner.last_block()))

    # Block Receiving Event
    def receive_block(event):

        miner = InputsConfig.NODES[event.block.miner]
        minerId = miner.id
        currentTime = event.time
        blockPrev = event.block.previous  # previous block id
        node: Node = InputsConfig.NODES[event.node]  # recipint
        event.block.rx_timestamp[node.id] = currentTime # TODO: <- Careful this will override block creation time for all nodes
        lastBlockId = node.last_block()  # the id of last block

        if InputsConfig.print_progress:
            print("Node " + str(node.id) + " received block " + str(event.block.id) + " from node " + str(minerId) + " at time " + str(currentTime) + " with previous block " + str(blockPrev) + " and last block " + str(lastBlockId) 
            + " with references " + str(event.block.references))
            print(str(node))
            
        # > case 1: the received block is built on top of the last block according to the recipient's blockchain ####
        if blockPrev == lastBlockId:
            # append the block to local blockchain
            # node.blockchain.append(event.block)

            references = [] if not hasattr(event.block, 'references') else event.block.references
            node.blockDAG.add_block(event.block.id, event.block.previous, references, event.block)

            BlockCommit.update_transactionsPool(node, event.block, currentTime)

            # remove block from forkedBlocks blockchain if it is there
            included_blocks = references + [event.block.id]
            # for included_block_id in included_blocks:
            #    BlockCommit.remove_included_block_from_forks(node, included_block_id)
            # Start mining or working on the next block

            BlockCommit.exclude_referenced_blocks_from_forkedBlocks_and_mempool(node, included_blocks, currentTime)


            BlockCommit.generate_next_block(node, currentTime)

            # Add block to fork candidates if it is not already there
            
            # node.forkedBlockCandidates += [event.block]

         # > case 2: the received block is  not built on top of the last block --> either we need to sync the state of the chain to that block
         # or it is a forked block if we are already passed that
        else:
            
            depth = event.block.depth + 1

            # We are behind, sync the state
            if (depth > node.blockDAG.get_depth()):
                BlockCommit.update_local_blockchain(node, miner, currentTime)
                # Start mining or working on the next block
                BlockCommit.generate_next_block(node, currentTime)

                node.forkedBlockCandidates += [event.block]

            # Block arrives at the same depth as the current block
            elif (depth == node.blockDAG.get_depth()):
                # Received block or current head may be forked
                candidates = node.blockDAG.find_fork_candidates_id(depth)

                BlockCommit.update_transactionsPool(node, event.block, currentTime)

                # # Add block to local blockDAG
                # ret_add = node.blockDAG.add_block(event.block.id, event.block.previous, event.block.references, event.block)
                # if not ret_add:
                #     BlockCommit.update_local_blockchain(node, miner, currentTime)
                    
        candidates = node.blockDAG.find_fork_candidates_id(event.block.depth + 1)
        blocks = [node.blockDAG.get_blockData_by_hash(id) for id in candidates]
        blocks += [event.block]
        node.forkedBlockCandidates += blocks

        # HACK: Remove duplicates from forkedBlockCandidates
        node.forkedBlockCandidates = list(set(node.forkedBlockCandidates))
                
    # Upon generating or receiving a block, the miner start working on the next block as in POW
    def generate_next_block(node : Node, currentTime):
        if node.hashPower > 0:
            # time when miner x generate the next block
            blockTime = currentTime + c.Protocol(node)
            BlockDAGScheduler.create_block_event(node, blockTime)

    def generate_initial_events():
        currentTime = 0
        for node in InputsConfig.NODES:
            BlockCommit.generate_next_block(node, currentTime)

    def propagate_block(block):
        for recipient in InputsConfig.NODES:
            if recipient.id != block.miner:
                # draw block propagation delay from a distribution !! or you can assign 0 to ignore block propagation delay
                blockDelay = Network.block_prop_delay()
                print("Propagating block " + str(block.id) + " from node " + str(block.miner) + " to node " + str(recipient.id) + " with delay " + str(blockDelay))
                Scheduler.receive_block_event(recipient, block, blockDelay)

    # Update local blockchain, if necessary, upon receiving a new valid block
    def update_local_blockchain(node, miner, currentTime):
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
        node.blockchain = [1,2,3,4,5,6,7,8,9,10,11]
        """

        # the node here is the one that needs to update its blockchain, while miner here is the one who owns the last block generated
        # the node will update its blockchain to mach the miner's blockchain

        # for i in range(len(node.blockchain), max( len(node.blockchain), depth)):
        # This doesn't really work to sync a blockDAG to sync we need:
        # 1. check if the block is in the blockDAG
        # 2. if it is, check if it is in the right order
        if node.blockDAG.get_depth() < miner.blockDAG.get_depth():
            missing_blocks = BlockDAGraphComparison.get_differing_blocks(node.blockDAG, miner.blockDAG)


            # Order missing blocks by depth, otherwise we might try to add a block that references a block that hasn't been added yet
            missing_blocks = sorted(missing_blocks, key=lambda block: max(node.blockDAG.get_depth_of_block(block), miner.blockDAG.get_depth_of_block(block)))
            
            for block_id in missing_blocks:
                # remove transactions from the mempool pool that are included in the new block
                block_data = miner.blockDAG.get_blockData_by_hash(block_id)

                BlockCommit.update_transactionsPool(node, block_data, currentTime)
                references = [] if not hasattr(block_data, 'references') else block_data.references

                # exclude blocks referenced by the new block from the forkedBlocks blockchain
                BlockCommit.exclude_referenced_blocks_from_forkedBlocks_and_mempool(node, references, currentTime)

                node.blockDAG.add_block(block_id, block_data.previous, references, block_data)

            # TODO: Add transactions to the mempool pool that are included in forked block

    def remove_included_block_from_forks(node, block_id):
        for block in node.forkedBlockCandidates:
            if block.id == block_id:
                print("Removing block from forkedBlockCandidates: " + str(block.id))
                node.forkedBlockCandidates.remove(block)
                break
    
    def exclude_referenced_blocks_from_forkedBlocks_and_mempool(node, references, currentTime):
        for blockId in references:
            BlockCommit.remove_included_block_from_forks(node, blockId)

            # Remove transactions from the mempool pool that are included in the new block
            blockData = node.blockDAG.get_blockData_by_hash(blockId) 

            if blockData is not None:
                BlockCommit.update_transactionsPool(node, blockData, currentTime)

    # Update local blockchain, if necessary, upon receiving a new valid block. This method is only triggered if Full technique is used
    def update_transactionsPool(node, block, currentTime):
        if InputsConfig.hasTrans and InputsConfig.Ttechnique == "Full":
            block_dict = {t.id: t for t in block.transactions}
            # I think some transactions cannot be deleted from the pool, because they are not in the pool "time-wise"
            # Filter by time otherwise we remove transactions that are not in the pool
            filtered_minerpool = [tx for tx in node.transactionsPool if tx.timestamp[1] <= currentTime]

            if InputsConfig.print_progress:
                print("Old pool size: ", len(filtered_minerpool))

            filtered_minerpool = [t for t in filtered_minerpool if t.id not in block_dict]
        
            if InputsConfig.print_progress:
                print("New pool size: ", len(filtered_minerpool))

            other_transactions = [tx for tx in node.transactionsPool if tx.timestamp[1] > currentTime]
            node.transactionsPool = [t for t in filtered_minerpool if t.id not in block_dict] + other_transactions
            
