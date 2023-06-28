import io
import os
import pickle
import unittest

from Models.BlockDAG.BlockDAGraph import BlockDAGraph


class TestBlockDAG_RunResult(unittest.TestCase):
    # In this class we check some of the consensus properties of the BlockDAG
    # We do this by loading a BlockDAG from a file and checking the properties
    def test_save_and_load_blockDAG(self):
        graph = BlockDAGraph()
        graph.add_block(0, -1, [])
        graph.add_block(1, 0, [])
        graph.add_block(2, 1, [])
        graph.save_graph_to_file("node_0.pkl")

        blockDAG : BlockDAGraph =  CustomUnpickler(open("node_0.pkl", "rb")).load()
        blockDAG.plot()
        


class CustomUnpickler(pickle.Unpickler):

    def find_class(self, module, name):
        if name == 'BlockDAGraph':
            from blocksim.src.Models.BlockDAG.BlockDAGraph import BlockDAGraph
            return BlockDAGraph

        return super().find_class(module, name)