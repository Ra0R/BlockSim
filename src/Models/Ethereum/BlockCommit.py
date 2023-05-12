from InputsConfig import InputsConfig as InputsConfig
from Models.BlockCommit import BlockCommit as BaseBlockCommit
from Models.Ethereum.Consensus import Consensus as c
from Models.Ethereum.Node import Node
from Models.Ethereum.Transaction import FullTransaction as FT
from Models.Ethereum.Transaction import LightTransaction as LT
from Models.Network import Network
from Scheduler import Scheduler
from Statistics import Statistics


class BlockCommit(BaseBlockCommit):

    # Handling and running Events
    def handle_event(event):
        if event.type == "create_block":
            BlockCommit.generate_block(event)
        elif event.type == "receive_block":
            BlockCommit.receive_block(event)

    # Block Creation Event
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
                    blockTrans, blockSize = FT.execute_transactions(
                        miner, eventTime)

                event.block.transactions = blockTrans
                event.block.usedgas = blockSize

            if InputsConfig.hasUncles:
                BlockCommit.update_unclechain(miner)
                blockUncles = Node.add_uncles(miner)  # add uncles to the block
                # (only when uncles activated)
                event.block.uncles = blockUncles

            miner.blockchain.append(event.block)

            if InputsConfig.hasTrans and InputsConfig.Ttechnique == "Light":
                LT.create_transactions()  # generate transactions
            BlockCommit.propagate_block(event.block)
            # Start mining or working on the next block
            BlockCommit.generate_next_block(miner, eventTime)

    # Block Receiving Event
    def receive_block(event):

        miner = InputsConfig.NODES[event.block.miner]
        minerId = miner.id
        currentTime = event.time
        blockPrev = event.block.previous  # previous block id

        node = InputsConfig.NODES[event.node]  # recipint
        lastBlockId = node.last_block().id  # the id of last block

        #### case 1: the received block is built on top of the last block according to the recipient's blockchain ####
        if blockPrev == lastBlockId:
            # append the block to local blockchain
            node.blockchain.append(event.block)

            if InputsConfig.hasTrans and InputsConfig.Ttechnique == "Full":
                BaseBlockCommit.update_transactionsPool(node, event.block)

            # Start mining or working on the next block
            BlockCommit.generate_next_block(node, currentTime)

         #### case 2: the received block is  not built on top of the last block ####
        else:
            depth = event.block.depth + 1
            if (depth > len(node.blockchain)):
                BlockCommit.update_local_blockchain(node, miner, depth)
                # Start mining or working on the next block
                BlockCommit.generate_next_block(node, currentTime)

            #### 2- if depth of the received block <= depth of the last block, then reject the block (add it to unclechain) ####
            else:
                uncle = event.block
                node.unclechain.append(uncle)

            if InputsConfig.hasUncles:
                BlockCommit.update_unclechain(node)
            if InputsConfig.hasTrans and InputsConfig.Ttechnique == "Full":
                # not sure yet.
                BaseBlockCommit.update_transactionsPool(node, event.block)

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

    def update_local_blockchain(node, miner, depth):
        # the node here is the one that needs to update its blockchain, while miner here is the one who owns the last block generated
        # the node will update its blockchain to mach the miner's blockchain
        from InputsConfig import InputsConfig as InputsConfig
        i = 0
        while (i < depth):
            if (i < len(node.blockchain)):
                # and (self.node.blockchain[i-1].id == Miner.blockchain[i].previous) and (i>=1):
                if (node.blockchain[i].id != miner.blockchain[i].id):
                    # move block to unclechain
                    node.unclechain.append(node.blockchain[i])
                    newBlock = miner.blockchain[i]
                    node.blockchain[i] = newBlock
                    if InputsConfig.hasTrans and InputsConfig.Ttechnique == "Full":
                        BaseBlockCommit.update_transactionsPool(node, newBlock)
            else:
                newBlock = miner.blockchain[i]
                node.blockchain.append(newBlock)
                if InputsConfig.hasTrans and InputsConfig.Ttechnique == "Full":
                    BaseBlockCommit.update_transactionsPool(node, newBlock)
            i += 1

    # Upon receiving a block, update local unclechain to remove all uncles included in the received block
    def update_unclechain(node):
        # remove all duplicates uncles in the miner's unclechain
        a = set()
        x = 0
        while x < len(node.unclechain):
            if node.unclechain[x].id in a:
                del node.unclechain[x]
                x -= 1
            else:
                a.add(node.unclechain[x].id)
            x += 1

        j = 0
        while j < len(node.unclechain):
            for k in node.blockchain:
                if node.unclechain[j].id == k.id:
                    del node.unclechain[j]  # delete uncle after inclusion
                    j -= 1
                    break
            j += 1

        j = 0
        while j < len(node.unclechain):
            c = "t"
            for k in node.blockchain:
                u = 0
                while u < len(k.uncles):
                    if node.unclechain[j].id == k.uncles[u].id:
                        del node.unclechain[j]  # delete uncle after inclusion
                        j -= 1
                        c = "f"
                        break
                    u += 1
                if c == "f":
                    break
            j += 1
