
import json

from InputsConfig import InputsConfig
from Models.Bitcoin.Consensus import \
    Consensus  # Careful, there are multiple Consensus classes
from Models.Transaction import Transaction
from RecordedBlock import MempoolOfNode, RecordedBlock, RecordedTransaction

WITH_TRANSACTION = False
ONLY_TRANSACTION_IDS = True

class ResultWriter:
    ############
    # TODO: Add the following to the result file:
    # - A file per node with the following information:
    #   - The node's mempool
    #   - The node's chain
    #
    # - A file with the following information:
    #   - The main chain
    #
    # - A file with all the transactions
    ############

    def writeResult():

        blocks = ResultWriter.get_main_chain()
        ResultWriter.write_blocks(blocks, with_transactions=WITH_TRANSACTION)

        # forks =  ResultWriter.get_forked_blocks(blocks, ResultWriter.get_all_blocks())
        forks = ResultWriter.get_forked_blocks()
        # print("Forks: ")
        #print(forks)
        ResultWriter.write_forks(forks, with_transactions=WITH_TRANSACTION)

        # mempools = ResultWriter.get_mempools()
        # for mempool in mempools:
        #     ResultWriter.write_mempool(mempool)

    def writeEvents(events, with_transactions=False):
        if not with_transactions:
            for event in events:
                event.block.transactions = []
        ResultWriter.write_json(InputsConfig.RESULTS_PATH + 'events.json', events)

    @staticmethod
    def write_json(filename, data):
        with open(filename, 'w') as f:
            f.write(json.dumps(data, default=lambda o: o.__dict__, indent=4))

    @staticmethod
    def write_blocks(blocks : list[RecordedBlock], with_transactions=False):

        if not with_transactions:
            blocks = ResultWriter.remove_transactions_from_blocks(blocks)
            
        ResultWriter.write_json(InputsConfig.RESULTS_PATH + 'mainchain.json', blocks)

    @staticmethod
    def write_forks(forks, with_transactions=False):
        if not with_transactions:
            forks = ResultWriter.remove_transactions_from_blocks(forks)

        ResultWriter.write_json(InputsConfig.RESULTS_PATH + 'forks.json', forks)

    @staticmethod
    def remove_transactions_from_blocks(blocks : list[RecordedBlock]) -> list[RecordedBlock]:
        for block in blocks:
            if ONLY_TRANSACTION_IDS:
                block.transactions = [transaction.hash for transaction in block.transactions]
            else:
                block.transactions = []

        return blocks

    @staticmethod
    def write_mempool(mempool : MempoolOfNode):
        ResultWriter.write_json(InputsConfig.RESULTS_PATH + str(mempool.node) + '-mempool.json', mempool)

    @staticmethod
    def write_transactions(transactions):
        ResultWriter.write_json(InputsConfig.RESULTS_PATH + 'transactions.json', transactions)



    @staticmethod
    def transaction_to_recorded_transaction(transaction: Transaction) -> RecordedTransaction:
        return RecordedTransaction(
            sender=transaction.sender,
            to=transaction.to,
            hash=transaction.id,
            size=transaction.size,
            fee=transaction.fee,
            timestamp=transaction.timestamp,
            value=transaction.value,
            nonce=""
            # nonce = transaction.nonce
        )
    
    @staticmethod
    def block_to_recorded_block(block) -> RecordedBlock:
        if block == []:
            return None
        if InputsConfig.model == 1:
            return RecordedBlock(
                block_hash = block.id,
                block_parent_hash = block.previous,
                block_number = block.depth,
                block_timestamp = block.timestamp,
                block_miner = block.miner,
                block_transaction_count = len(block.transactions),
                block_size = block.size,
                transactions = [ResultWriter.transaction_to_recorded_transaction(transaction) for transaction in block.transactions]
            )
        if InputsConfig.model == 4:
            for node in InputsConfig.NODES:
                if not node.blockDAG.get_blockData_by_hash(block) == None:
                    block = InputsConfig.NODES[0].blockDAG.get_blockData_by_hash(block)
            
            return RecordedBlock(
                block_hash = block.id,
                block_parent_hash = block.previous,
                block_number = block.depth,
                block_timestamp = block.timestamp,
                block_miner = block.miner,
                block_transaction_count = len(block.transactions),
                block_size = block.size,
                transactions = [ResultWriter.transaction_to_recorded_transaction(transaction) for transaction in block.transactions]
            )
    # TODO Move to consesus
    def get_mempools(beforetime=InputsConfig.simTime) -> list[MempoolOfNode]:
        mempools : list[MempoolOfNode] = []
        for node in InputsConfig.NODES:
            mempool = MempoolOfNode(
                node = node.id,
                mempool =  [ResultWriter.transaction_to_recorded_transaction(transaction) for transaction in node.transactionsPool if transaction.timestamp[1] < beforetime] 
            )
            mempools.append(mempool)
        return mempools

    def get_main_chain() -> list[RecordedBlock]:
        main_chain : list[RecordedBlock] = []
        if InputsConfig.model == 1:
            for block in Consensus.global_main_chain:
                main_chain.append(ResultWriter.block_to_recorded_block(block))
        if InputsConfig.model == 4:
            node = InputsConfig.NODES[0]
            main_chain = [ResultWriter.block_to_recorded_block(block) for block in node.blockDAG.get_main_chain()]
        
        return main_chain    

    def get_all_blocks() -> list[RecordedBlock]:
        blocks : list[RecordedBlock] = []
        for node in InputsConfig.NODES:
            for block in node.blockchain:
                blocks.append(ResultWriter.block_to_recorded_block(block))
        return blocks

    def get_forked_blocks() -> list[RecordedBlock]:
        forked_blocks : list[RecordedBlock] = []
        for node in InputsConfig.NODES:
            forked_blocks_by_node = []


            if InputsConfig.model == 4:
                list_of_all_block_hashes = node.blockDAG.to_list()
                main_chain = node.blockDAG.get_main_chain()
                forked_block_ids = [block for block in list_of_all_block_hashes if block not in main_chain]
                f_blocks = [node.blockDAG.get_blockData_by_hash(block) for block in forked_block_ids]
                forked_blocks_by_node = [ResultWriter.block_to_recorded_block(block) for block in f_blocks]
                
            if InputsConfig.model == 1:
                forked_blocks_by_node = [ResultWriter.block_to_recorded_block(
                    block) for block in node.forkedBlocks if block.depth > 0]
                
            if(len(forked_blocks_by_node) > 0):
                forked_blocks = forked_blocks  + forked_blocks_by_node

            # Remove duplicate blocks by hash
            forked_blocks = list({block.block_hash: block for block in forked_blocks}.values())
        return forked_blocks