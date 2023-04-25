from Models.BlockDAG.BlockDAG import BlockDAG
from Models.Node import Node as BaseNode


class Node(BaseNode):
    def __init__(self, id, hashPower):
        '''Initialize a new miner named name with hashrate measured in hashes per second.'''
        super().__init__(id)  # ,blockchain,transactionsPool,blocks,balance)
        self.hashPower = hashPower
        # self.blockchain = []  # create an array for each miner to store chain state locally
        
        self.blockDAG : BlockDAG = BlockDAG()
        self.transactionsPool = []
        self.blocks = 0  # total number of blocks mined in the main chain
        self.balance = 0  # to count all reward that a miner made, including block rewards + uncle rewards + transactions fees
        self.forkedBlocks = []
        self.isLeader = False


    """
    VT(tx) = True if tx is valid, False otherwise
    This method is used to verify if a transaction can extend the current blockchain
    Validity:
    - Correct signature
    - Correct inputs
    - Correct outputs
    - Correct fee
    - Transaction is not a double-spend
    - Transaction is not executed twice
    """
    def validate_transaction(self, transaction, blockchain):
        return True

    """
    VB(block) = True if block is valid, False otherwise
    This method is used to verify if a block is valid and can extend the current blockchain
    Validity:
    - Correct PoW
    - Valid transactions (VB(B) = True => VT(T) = True for all T in B)
    - Atleast one valid transaction 
    """
    def validate_block(self, block, blockchain):
        return True

    """
    FB()
    This method is used to fill a block with valid transactions
    """
    def fill_block(self, block, transactions):
        for tx in transactions:
            if self.validate_transaction(tx, block.blockchain):
                block.transactions.append(tx)
                block.size += tx.size
                block.fee += tx.fee
                block.reward += tx.reward
                block.num_txs += 1
                block.num_valid_txs += 1
            else:
                block.num_invalid_txs += 1
        return block
