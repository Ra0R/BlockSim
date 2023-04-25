import unittest

from blocksim.src.Models.BlockDAG.BlockDAGraph import BlockDAGraph


class TestBlockDAG_DataStructure(unittest.TestCase):
    def test_create_graph(self):
        blockDAG = BlockDAGraph()

        # Add genesis block
        blockDAG.add_block(0, [])

        
