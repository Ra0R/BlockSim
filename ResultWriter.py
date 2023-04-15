
from blocksim.Models.Consensus import Consensus


class ResultWriter:
    blocks=[]  
    transactions=[]


    def __init__(self, blocks, transactions):
        

        self.blocks = blocks
        self.transactions = transactions
        