import copy
import operator
import random

import numpy as np
from InputsConfig import InputsConfig as InputsConfig
from Models.Network import Network


def profile(f): return f


class Transaction(object):

    """ Defines the Ethereum Block model.

    :param int id: the uinque id or the hash of the transaction
    :param int timestamp: the time when the transaction is created. In case of Full technique, this will be array of two value (transaction creation time and receiving time)
    :param int sender: the id of the node that created and sent the transaction
    :param int to: the id of the recipint node
    :param int value: the amount of cryptocurrencies to be sent to the recipint node
    :param int size: the transaction size in MB
    :param int gasLimit: the maximum amount of gas units the transaction can use. It is specified by the submitter of the transaction
    :param int usedGas: the amount of gas used by the transaction after its execution on the EVM
    :param int gasPrice: the amount of cryptocurrencies (in Gwei) the submitter of the transaction is willing to pay per gas unit
    :param float fee: the fee of the transaction (usedGas * gasPrice)
    """

    def __init__(self,
	 id=0,
	 timestamp=0 or [],
	 sender=0,
         to=0,
         value=0,
	 size=0.000546,
         fee=0):

        self.id = id
        self.timestamp = timestamp
        self.sender = sender
        self.to= to
        self.value=value
        self.size = size
        self.fee= fee


class LightTransaction():

    pending_transactions=[] # shared pool of pending transactions

    def create_transactions():

        LightTransaction.pending_transactions=[]
        pool= LightTransaction.pending_transactions
        Psize= int(InputsConfig.Tn * InputsConfig.Binterval)


        for i in range(Psize):
            # assign values for transactions' attributes. You can ignore some attributes if not of an interest, and the default values will then be used
            tx= Transaction()

            tx.id= random.randrange(100000000000)
            tx.sender = random.choice (InputsConfig.NODES).id
            tx.to= random.choice (InputsConfig.NODES).id
            tx.size= random.expovariate(1/InputsConfig.Tsize)
            tx.fee= random.expovariate(1/InputsConfig.Tfee)

            pool += [tx]


        random.shuffle(pool)


    ##### Select and execute a number of transactions to be added in the next block #####
    def execute_transactions():
        transactions= [] # prepare a list of transactions to be included in the block
        size = 0 # calculate the total block gaslimit
        count=0
        blocksize = InputsConfig.Bsize
        pool= LightTransaction.pending_transactions

        pool = sorted(pool, key=lambda x: x.fee, reverse=True) # sort pending transactions in the pool based on the gasPrice value

        while count < len(pool):
                if  (blocksize >= pool[count].size):
                    blocksize -= pool[count].size
                    transactions += [pool[count]]
                    size += pool[count].size
                count+=1

        return transactions, size

class FullTransaction():

    def create_transactions():
        Psize= int(InputsConfig.Tn * InputsConfig.simTime)

        for i in range(Psize):
            # assign values for transactions' attributes. You can ignore some attributes if not of an interest, and the default values will then be used
            tx= Transaction()

            tx.id= random.randrange(100000000000)
            creation_time= random.randint(0,InputsConfig.simTime-1)
            receive_time= creation_time
            tx.timestamp= [creation_time,receive_time]
            sender= random.choice (InputsConfig.NODES)
            tx.sender = sender.id
            tx.to= random.choice (InputsConfig.NODES).id
            tx.size= random.expovariate(1/InputsConfig.Tsize)
            tx.fee= random.expovariate(1/InputsConfig.Tfee)

            sender.transactionsPool.append(tx)
            FullTransaction.transaction_prop(tx)

    # Transaction propogation & preparing pending lists for miners
    def transaction_prop(tx):
        # Fill each pending list. This is for transaction propogation
        for node in InputsConfig.NODES:
            if tx.sender != node.id:
                t= copy.deepcopy(tx)
                t.timestamp[1] = t.timestamp[1] + Network.tx_prop_delay() # transaction propogation delay in seconds
                node.transactionsPool.append(t)


    @profile
    def execute_transactions(miner,currentTime):
        transactions= [] # prepare a list of transactions to be included in the block
        size = 0 # calculate the total block gaslimit
        blocksize = InputsConfig.Bsize

        filtered_minerpool = [tx for tx in miner.transactionsPool if tx.timestamp[1] <= currentTime]
        pool = sorted(filtered_minerpool, key=lambda x: x.fee, reverse=True) # sort pending transactions in the pool based on the gasPrice value

        # pool : list of transactions in the pool of the miner
        # tx1 = { id: 1, timestamp: [0,0], sender: 1, to: 2, value: 100, size: 0.000546, fee: 3}
        # tx2 = { id: 2, timestamp: [0,0], sender: 1, to: 3, value: 100, size: 0.000546, fee: 2}
        # tx3 = { id: 3, timestamp: [0,0], sender: 1, to: 4, value: 100, size: 0.000546, fee: 1}
        # pool = [tx1, tx2, tx3]
        
        # I think this will always iterate through the entire pool
        # while count < len(pool):
        #         if  (blocksize >= pool[count].size and pool[count].timestamp[1] <= currentTime):
        #             blocksize -= pool[count].size
        #             transactions += [pool[count]]
        #             size += pool[count].size
        #         count+=1

        # Show length of transactions that are not eligible
        # print("Transactions not eligible: ")
        # print(len(pool) - len([tx for tx in pool if tx.timestamp[1] <= currentTime]))
        

        for tx in pool:
            if blocksize <= 0:
                break

            if  (blocksize >= tx.size):
                blocksize -= tx.size
                transactions.append(tx)
                size += tx.size

        return transactions, size
