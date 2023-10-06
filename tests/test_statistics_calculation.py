import unittest
from blocksim.src.Models.BlockDAG.BlockDAGraph import BlockDAGraph

from blocksim.tests.mock.mock_block import MockBlock
from blocksim.tests.mock.mock_thesisstats import ThesisStats

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
        
    def test_throughput(self):
        blockDAG = BlockDAGraph()
        tx1 = Transaction(1, 2, 3, 4, 5, 6)
        tx2 = Transaction(2, 2, 3, 4, 5, 6,)
        tx3 = Transaction(3, 2, 3, 4, 5, 6,)
        tx4 = Transaction(4, 2, 3, 4, 5, 6,)
        tx5 = Transaction(5, 2, 3, 4, 5, 6,)
        tx6 = Transaction(6, 2, 3, 4, 5, 6,)
        tx7 = Transaction(7, 2, 3, 4, 5, 6,)
        tx8 = Transaction(8, 2, 3, 4, 5, 6,)
        tx9 = Transaction(9, 2, 3, 4, 5, 6,)
        tx10 = Transaction(10, 2, 3, 4, 5, 6,)
        tx11 = Transaction(11, 2, 3, 4, 5, 6,)
        tx12 = Transaction(12, 2, 3, 4, 5, 6,)
        tx13 = Transaction(13, 2, 3, 4, 5, 6,)
        tx14 = Transaction(14, 2, 3, 4, 5, 6,)
        tx15 = Transaction(15, 2, 3, 4, 5, 6,)

        # Add genesis block
        # Block 0
        block_data_0 = MockBlock(0, 0, 1, [1, 1, 1], 1, [tx1, tx2, tx3], 1, previous=-1, references=[])
        blockDAG.add_block(0, -1, [], block_data_0)
        # Block 1
        block_data_1 = MockBlock(1, 1, 2, [2, 2, 2], 2, [tx4, tx5, tx6], 1, 0, [])
        blockDAG.add_block(1, 0, [], block_data_1)
        # Block 2
        block_data_2 = MockBlock(2, 2, 3, [3, 3, 3], 3, [tx7, tx8, tx9], 1, 1, [])
        blockDAG.add_block(2, 1, [], block_data_2)
        # Block 3
        block_data_3 = MockBlock(2, 3, 4, [4, 4, 4], 4, [tx9, tx8, tx12], 1, 1, [])
        blockDAG.add_block(3, 1, [], block_data_3)
        # Block 4
        block_data_4 = MockBlock(3, 4, 5, [5, 5, 5], 5, [tx13, tx14, tx15], 1, 2, [3])
        blockDAG.add_block(4, 2, [3], block_data_4)

        # Ascii Graph:
        #  0       --- Depth 0
        #  |
        #  1       --- Depth 1
        # / \
        # 2 3      --- Depth 2
        # \ :
        #   4      --- Depth 3

        # This graph has one fork which is block 3
        # reference_inclusion_rate = 1/3
        # conflict inclusion rate is 2/3 (since transactions [8,9] are conflicting in blocks 2 and 3)

        # conflict_time to inclusion for block 3 transactions is 0
        # reference_time to inclusion for block 3 transactions is 1

        inclusion_matrix = ThesisStats.calculate_transaction_time_to_inclusion(blockDAG)
        print(inclusion_matrix)
        inclusion_rates = ThesisStats.calculate_inclusion_rates(inclusion_matrix, blockDAG)

        print(inclusion_rates)
        # inclusion_rate_per_block = ThesisStats.calculate_inclusion_rate_per_block(inclusion_matrix)
        # self.assertTrue(inclusion_rates["fork_id"][0] == 3)
        # self.assertAlmostEqual(inclusion_rates["conflict_inclusion_rate"][0], 2/3)
        # self.assertAlmostEqual(inclusion_rates["reference_inclusion_rate"][0], 1/3)
        # self.assertTrue(inclusion_rates["time_to_inclusion_avg"][0] == 0)
        # self.assertTrue(inclusion_rates["time_to_reference_avg"][0] == 1)
        main_chain = blockDAG.get_main_chain()
        list_of_all_block_hashes = blockDAG.get_topological_ordering()

        transaction_troughput_sim, transaction_troughput_real = ThesisStats.calculate_transaction_troughput2(blockDAG,
            main_chain, list_of_all_block_hashes, 100)
        