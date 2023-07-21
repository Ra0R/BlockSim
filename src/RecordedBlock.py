
import json
from typing import Optional

from dataclasses import dataclass


@dataclass
class RecordedTransaction:
    sender: str # "from" is a reserved word
    to: str
    hash: str # Id
    size: str
    fee: str
    timestamp: str
    value : str
    nonce: Optional[str]

@dataclass
class MempoolOfNode:
    node: str
    mempool: list[RecordedTransaction] # Do we need to distinguish between mempool and block transactions?

@dataclass
class RecordedBlock:
    block_hash: str
    block_parent_hash: str
    block_number: int
    block_timestamp: int
    block_miner: str
    block_transaction_count: int
    transactions: list[RecordedTransaction]
    block_size: str
    # block_nonce: int
    # block_transaction_count: int

    def read_json_file(filename):
        with open(filename) as f:
            data = json.load(f)
        return data
    
    def from_json(self, filename):
        json = RecordedBlock.read_json_file(filename)

        transactionJson = json["transactions"]
        transactions = []
        for transaction in transactionJson:
            transactions.append(RecordedTransaction(transaction))

        return RecordedBlock(
            block_hash=json["block_hash"],
            block_parent_hash=json["block_parent_hash"],
            block_timestamp=json["block_timestamp"],
            # block_miner="none", # TODO this doesn't exist on listener, do we need it?
            transactions=transactions
        )
    
    @dataclass
    class Stats:
        block_count: int
        fork_count: int
        fork_rate: float
        mempool_similarity_matrix: list[list[float]]
        
        
