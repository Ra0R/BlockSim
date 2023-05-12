import unittest


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
        self.to = to
        self.value = value
        self.size = size
        self.fee = fee

class Test_Statistics_Calculation(unittest.TestCase):

    def test_Intersection_of_Transactions(self):
        tx1 = Transaction(
            1,
            2,
            3,
            4,
            5,
            6,  
        )
        tx2 = Transaction(
            2,
            2,
            3,
            4,
            5,
            6,
        )

        tx3 = Transaction(
            1,
            2,
            3,
            4,
            5,
            6)
        
        tx4 = Transaction(
            3,
            2,
            3,
            4,
            5,
            6,
        )

        set1 = set([tx1, tx2])
        set2 = set([tx3, tx4])
        intersection_ids = set([tx.id for tx in set1]).intersection([tx.id for tx in set2])
        intersection = [tx for tx in set1 if tx.id in intersection_ids]
        self.assertTrue(len(intersection) == 1)
        self.assertTrue(intersection[0].id == 1)
        
