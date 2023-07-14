import unittest

from blocksim.src.Models.BlockDAG.BlockDAGraph import (BlockDAGraph,
                                                       BlockDAGraphComparison)
from blocksim.tests.mock.mock_block import MockBlock
from blocksim.tests.mock.mock_thesisstats import ThesisStats
from blocksim.tests.mock.mock_transaction import Transaction


class TestBlockDAG_DataStructure(unittest.TestCase):

    def get_test_graph(self):
        blockDAG = BlockDAGraph()

        # Add genesis block
        blockDAG.add_block(0, -1, [])

        blockDAG.add_block(1, 0, [])
        blockDAG.add_block(2, 1, [])
        blockDAG.add_block(3, 1, [])
        blockDAG.add_block(4, 2, [3])

        # Ascii Graph:
        #  0
        #  |
        #  1
        # / \
        # 2 3
        # \ :
        #   4

        return blockDAG

    def test_create_graph(self):
        blockDAG = self.get_test_graph()
        blockDAG.plot()

    def test_graph_same(self):
        blockDAG = self.get_test_graph()
        blockDAG2 = self.get_test_graph()
        self.assertTrue(BlockDAGraphComparison.equal(blockDAG, blockDAG2))

    def test_graph_different(self):
        blockDAG = self.get_test_graph()
        blockDAG2 = self.get_test_graph()
        blockDAG2.add_block(4, 3, [])
        self.assertFalse(BlockDAGraphComparison.equal(blockDAG, blockDAG2))

    def test_get_differing_blocks(self):
        blockDAG = self.get_test_graph()
        blockDAG2 = self.get_test_graph()
        blockDAG2.add_block(5, 4, [])
        blockDAG2.plot()
        self.assertEqual(BlockDAGraphComparison.get_differing_blocks(blockDAG, blockDAG2), {5})

    def test_depth(self):
        blockDAG = self.get_test_graph()
        self.assertEqual(blockDAG.get_depth(), 3)

    def test_get_last_block(self):
        blockDAG = self.get_test_graph()
        self.assertEqual(blockDAG.get_last_block(), 4)

    def test_fork_candidates(self):
        blockDAG = self.get_test_graph()
        candidate_ids = blockDAG.find_fork_candidates_id(2)
        self.assertTrue(3 in candidate_ids)
        self.assertTrue(2 in candidate_ids)

    def test_get_descendants(self):
        blockDAG = self.get_test_graph()
        descendants = blockDAG.get_descendants(1)
        self.assertTrue(4 in descendants)
        self.assertTrue(3 in descendants)
        self.assertTrue(2 in descendants)

    def test_get_ancestors(self):
        BlockDAG = self.get_test_graph()

        descendants = BlockDAG.get_descendants(1)
        self.assertTrue(4 in descendants)
        self.assertTrue(3 in descendants)
        self.assertTrue(2 in descendants)
        print(descendants)

    def test_get_toplogical_sort(self):
        # Ascii Graph:
        #  0
        #  |
        #  1
        # / \
        # 2 3
        # \ :
        #   4

        blockDAG = self.get_test_graph()
        topological_sort = blockDAG.get_topological_ordering()
        topological_sort.reverse()
        self.assertEqual(topological_sort, [0, 1, 2, 3, 4])

    def test_is_in_chain_of_block(self):
        blockDAG = self.get_test_graph()
        self.assertTrue(blockDAG.is_in_chain_of_block(4, 1))
        self.assertTrue(blockDAG.is_in_chain_of_block(4, 0))
        self.assertTrue(blockDAG.is_in_chain_of_block(4, 3))
        self.assertTrue(blockDAG.is_in_chain_of_block(4, 2))
        self.assertFalse(blockDAG.is_in_chain_of_block(1, 4))
        self.assertFalse(blockDAG.is_in_chain_of_block(2, 4))
        self.assertFalse(blockDAG.is_in_chain_of_block(3, 4))
        self.assertFalse(blockDAG.is_in_chain_of_block(0, 4))

    def test_is_in_chain_of_block_extended(self):
        # Ascii Graph:
        #  0
        #  |
        #  1
        # / \
        # 2 3
        # | :
        # 4
        # |
        # 5
        # |
        # 6
        # |
        # 7
        # |
        # 8
        # |
        # 9

        blockDAG = self.get_test_graph()
        blockDAG.add_block(5, 4, [])
        blockDAG.add_block(6, 5, [])
        blockDAG.add_block(7, 6, [])
        blockDAG.add_block(8, 7, [])

        self.assertTrue(blockDAG.is_in_chain_of_block(5, 3))
        self.assertTrue(blockDAG.is_in_chain_of_block(6, 3))
        self.assertTrue(blockDAG.is_in_chain_of_block(7, 3))
        self.assertTrue(blockDAG.is_in_chain_of_block(8, 3))

    def test_refrence_to_refrence(self):
        # Ascii Graph:
        #  0
        #  |
        #  1
        # / \
        # 2  3
        # |  |
        # 4  7
        # |  ?
        # 6 New block to be created

        blockDAG = self.get_test_graph()

        blockDAG.add_block(7, 3, [])
        # blockDAG.add_block(6, 4, [3,7])
        self.assertTrue(blockDAG.is_in_chain_of_block(6, 3))
        # This is wrong because the previous refence is not in the chain of the new block
        # We should simulate this by adding a block that is not in the chain of the new block
        self.assertTrue(blockDAG.is_in_chain_of_block(7, 3))

    def test_simulation_reference(self):
        blockDAG = self.get_test_graph()

        blockDAG.add_block(7, 3, [])
        graph_sim = blockDAG.simluate_add_block(6, 4, [3, 7])

        self.assertTrue(blockDAG.is_in_chain_of_block(6, 3, graph_sim))
        self.assertTrue(blockDAG.is_in_chain_of_block(7, 3, graph_sim))

    def test_calculate_inclusion_rate(self):
        blockDAG = BlockDAGraph()
        tx1 = Transaction(1,2,3,4,5,6)
        tx2 = Transaction(2,2,3,4,5,6,)
        tx3 = Transaction(3,2,3,4,5,6,)
        tx4 = Transaction(4,2,3,4,5,6,)
        tx5 = Transaction(5,2,3,4,5,6,)
        tx6 = Transaction(6,2,3,4,5,6,)
        tx7 = Transaction(7,2,3,4,5,6,)
        tx8 = Transaction(8,2,3,4,5,6,)
        tx9 = Transaction(9,2,3,4,5,6,)
        tx10 = Transaction(10,2,3,4,5,6,)
        tx11 = Transaction(11,2,3,4,5,6,)
        tx12 = Transaction(12,2,3,4,5,6,)
        tx13 = Transaction(13,2,3,4,5,6,)
        tx14 = Transaction(14,2,3,4,5,6,)
        tx15 = Transaction(15,2,3,4,5,6,)

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

        # conflict_time to inclusion for block 3s transactions is 0
        # reference_time to inclusion for block 3s transactions is 1

        inclusion_matrix = ThesisStats.calculate_transaction_time_to_inclusion(blockDAG)
        print(inclusion_matrix)
        inclusion_rates = ThesisStats.calculate_inclusion_rates(inclusion_matrix, blockDAG)

        print(inclusion_rates)
        # inclusion_rate_per_block = ThesisStats.calculate_inclusion_rate_per_block(inclusion_matrix)
        self.assertTrue(inclusion_rates["fork_id"][0] == 3)
        self.assertAlmostEqual(inclusion_rates["conflict_inclusion_rate"][0], 2/3)
        self.assertAlmostEqual(inclusion_rates["reference_inclusion_rate"][0] , 1/3)
        self.assertTrue(inclusion_rates["time_to_inclusion_avg"][0] == 1/3)
        self.assertTrue(inclusion_rates["time_to_reference_avg"][0] == 1)
