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