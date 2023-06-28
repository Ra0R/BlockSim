import unittest

from blocksim.src.Models.BlockDAG.BlockDAGraph import (BlockDAGraph,
                                                       BlockDAGraphComparison)


class TestBlockDAG_DataStructure(unittest.TestCase):

    def get_test_graph(self):
        blockDAG = BlockDAGraph()

        # Add genesis block
        blockDAG.add_block(0, -1 , [])

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
        descendants = blockDAG.get_ancestors(1)
        self.assertTrue(4 in descendants)
        self.assertTrue(3 in descendants)
        self.assertTrue(2 in descendants)

    def test_get_ancestors(self):
        BlockDAG = self.get_test_graph()

        descendants = BlockDAG.get_ancestors(1)
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
        self.assertEqual(topological_sort, [0,1,2,3,4])

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
