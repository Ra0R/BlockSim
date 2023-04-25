class BlockDAGraph:
    def __init__(self):
        self.graph = {}


    def add_block(self, block, parents=[]):
        """
        Add a block to the DAG
        Parents is a list of blocks that this block references  (direct parents)
        Equivalent to previous block in a blockchain
        """
        self.graph[block] = set(parents)
        self.plot()

    def get_parents(self, block):
        return self.graph.get(block, set())

    def get_children(self, block):
        children = set()
        for b, parents in self.graph.items():
            if block in parents:
                children.add(b)
        return children
    
    def plot(self):
        import graphviz as gv
        import matplotlib.pyplot as plt

        graph = gv.Digraph(format='png')
        for block, parents in self.graph.items():
            graph.node(str(block), str(block))
            for parent in parents:
                graph.edge(str(parent), str(block))
        graph.render('blockDAG.gv', view=True)
        

    # TODO Get order of blocks
    def get_order(self):
        pass

