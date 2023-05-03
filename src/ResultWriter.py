
import json

from InputsConfig import InputsConfig
from Models.Bitcoin.Consensus import \
    Consensus  # Careful, there are multiple Consensus classes
from Models.Transaction import Transaction
from RecordedBlock import MempoolOfNode, RecordedBlock, RecordedTransaction

WITH_TRANSACTION = False

class ResultWriter:
    ############
    # TODO: Add the following to the result file:
    # - A file per node with the following information:
    #   - The node's mempool
    # TODO - Some kind of mempool comparison between nodes

    # TODO - A file with the nodes mempool before block creation
    
    # TODO (?) - A file with the nodes mempool after block creation
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

    def get_mempools() -> list[MempoolOfNode]:
        mempools : list[MempoolOfNode] = []
        for node in InputsConfig.NODES:
            mempool = MempoolOfNode(
                node = node.id,
                mempool =  [ResultWriter.transaction_to_recorded_transaction(transaction) for transaction in node.transactionsPool] 
            )
            mempools.append(mempool)
        return mempools

    def get_main_chain() -> list[RecordedBlock]:
        main_chain : list[RecordedBlock] = []
        for block in Consensus.global_main_chain:
                    main_chain.append(ResultWriter.block_to_recorded_block(block))

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
            forked_blocks_by_node = [ResultWriter.block_to_recorded_block(
                block) for block in node.forkedBlockCandidates]
            if(len(forked_blocks_by_node) > 0):
                forked_blocks = forked_blocks  + forked_blocks_by_node
        return forked_blocks