import unittest

from blocksim.tests.mock.mock_transaction import Transaction


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
        
