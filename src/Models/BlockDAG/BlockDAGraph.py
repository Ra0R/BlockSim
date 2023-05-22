from bloom_filter import BloomFilter


class BlockDAGraph:
    def __init__(self):
        self.graph = {}
        self.last_block = -1
        self.depth = 0 # Depth holds the max depth of the graph
        self.transaction_bloomfilter = BloomFilter(max_elements=100000, error_rate=0.1)

    def add_block(self, block_hash, parent, references=[], block=None):
        """
        Add a block to the DAG
        References is a list of abandoned blocks that this block references
        Previous is the block that this block is built on 
        """
        #[ {0: {parent: [], references: []}}, {1: {parent: [0], references: []}} ]

        # Get depth of parent and add 1
        # Add the block
        depth = 0
        if parent != -1:
            depth = self.graph[parent]["_depth"] + 1

        self.graph[block_hash] = {"parent": parent, "references": set(references), "block_data": block,  "_depth": depth}
        self.last_block = block_hash
        
        # Update depth
        self.depth = max(self.depth, depth)

        # Add transaction ids to bloom filter
        # if block != None:
        #     for transaction in block.transactions:
        #         self.transaction_bloomfilter.add(transaction.id)

    # def update_block(self, block_hash, references=[]):
    #     """
    #     Update a block in the DAG
    #     References is a list of abandoned blocks that this block references

    #     This method is used when a miner creates a block and wants to update the references
    #     TODO: Since blocks are not propagated to the miner itself
    #     """
    #     # Update the references
    #     self.graph[block_hash]["references"] = set(references)

    def find_fork_candidates_id(self, depth):
        """
        Find a block on the same depth as the given block
        """
        candidates = []
        for id, data in self.graph.items():
            if data["_depth"] == depth:
                candidates.append(id)
        
        return candidates
    

    def get_main_chain(self) -> list:
        """
        Get the main chain of the DAG
        """
        main_chain = []
        block_hash = self.last_block
        while block_hash != -1:
            main_chain.append(block_hash)
            block_hash = self.graph[block_hash]["parent"]
        main_chain.reverse()
        return main_chain

    def __str__(self):
        return "[" + ", ".join([str(block_hash) for block_hash in self.graph.keys()]) + "]"

    def get_depth(self):
        return self.depth

    def get_last_block(self):
        return self.last_block
    
    def plot(self):
        import graphviz as gv

        graph = gv.Digraph(format='png')
        # Graph previous as full edges and references as dashed edges
        for block_number, data in self.graph.items():
            parent = data["parent"]
            references = data["references"]

            # Add the block
            graph.node(str(block_number), str(block_number) 
                    #    + "\n |T|:" + str(len(data["block_data"].transactions))
                       ,
                        shape="box", fontname="Helvetica")

            if parent == -1:
                # Skip plotting
                graph.edge(str(block_number), str(parent), style="solid")
                graph.node(str("-1"), "Genesis", shape="box", fontname="Helvetica")
            else:
                # Add the parent
                graph.edge(str(block_number), str(parent), style="solid")

            # Add the references
            for reference in references:
                    graph.edge(str(block_number), str(reference), style="dashed")

        # Genesis is at top
        graph.attr(rankdir='BT')
        graph.render('blockchain.gv', view=True)

    def plot_with_inclusion_rate_per_block(self, inclusion_rate_per_block):
        """
        This graph plots the blockchain with the transaction inclusion matrix
        -> Red connections refer to transaction which are included in same height
        -> Blue connections refer to transactions which are included at different heights
        """
        import graphviz as gv

        graph = gv.Digraph(format='png')
        # Graph previous as full edges and references as dashed edges
        for block_number, data in self.graph.items():
            parent = data["parent"]
            references = data["references"]

            # Add the block
            graph.node(str(block_number), str(block_number) + "\n |T|:" +
                       str(len(data["block_data"].transactions)), shape="box", fontname="Helvetica")

            if parent == -1:
                # Skip plotting
                graph.edge(str(block_number), str(parent), style="solid")
                graph.node(str("-1"), "Genesis", shape="box", fontname="Helvetica")
            else:
                # Add the parent
                graph.edge(str(block_number), str(parent), style="solid")

            # Add the references
            for reference in references:
                graph.edge(str(block_number), str(reference), style="dashed")

        for i in range(len(inclusion_rate_per_block["fork_id"])):
            fork_id = inclusion_rate_per_block["fork_id"][i]
            block_id = inclusion_rate_per_block["block_id"][i]
            inclusion_rate = inclusion_rate_per_block["inclusion_rate"][i]
            inclusion_time = inclusion_rate_per_block["inclusion_time"][i]

            if fork_id == -1:
                continue

            # Depending on inclusion time draw a red or blue edge
            # Depending on inclusion rate draw a thicker edge
            tail_name = str(fork_id)
            head_name = str(block_id)
            penwidth = str(inclusion_rate * 5)
            arrowhead = "none"
            if inclusion_time == 0:
                color = "green"
            else:
                color = "blue"

            if inclusion_time < 0:
                color = "red"

            graph.edge(str(fork_id), str(block_id), color=color, penwidth=str(inclusion_rate * 5), arrowhead="none")

        # Genesis is at top
        graph.attr(rankdir='BT')
        graph.render('blockdag_inclusion.gv', view=True)

    def get_all_transaction_ids(self):
        """
        Get all transactions in the DAG
        """
        transactions = set()
        for _, data in self.graph.items():
            transactions = transactions.union([tx.id for tx in data["block_data"].transactions])
        
        return transactions

    def get_blockData_by_hash(self, block_hash):
        if block_hash == -1:
            return None
        
        if block_hash not in self.graph:
            return None
        
        return self.graph[block_hash]["block_data"]
    
    def get_descendants(self, block_hash):
        """ 
        Get all descendants of a block
        """
        descendants = set()

        # Add the block itself
        descendants.add(block_hash)

        # Add all descendants of the children
        for child_hash, data in self.graph.items():
            if data["parent"] == block_hash:
                descendants = descendants.union(self.get_descendants(child_hash))
        
        return descendants


    def block_exists(self, block_hash):
        return block_hash in self.graph

    def get_depth_of_block(self, block_hash):
        if self.block_exists(block_hash):
            return self.graph[block_hash]["_depth"]
        else:
            return -1
        
    def is_in_chain_of_block(self, block_hash, block_hash2):
        """ 
        Check if block2 is in the chain of block1
        """
        if block_hash == block_hash2:
            return True

        if block_hash == -1:
            return False

        return self.is_in_chain_of_block(self.graph[block_hash]["parent"], block_hash2)

    def to_list(self):
        """
        Convert the graph to a list of block hashes
        """

        return list(self.graph.keys())
    
    def get_reachable_blocks(self):
        """
        Get all blocks that are reachable from the last block
        through either references or parent
        """
        reachable_blocks = set()

        # Add the last block
        reachable_blocks.add(self.last_block)

        # Add all blocks that are referenced
        for _, data in self.graph.items():
            for reference in data["references"]:
                reachable_blocks.add(reference)
        
        # Add all blocks that are parents
        for _, data in self.graph.items():
            reachable_blocks.add(data["parent"])
        
        return reachable_blocks

    def get_topological_orderings(self):
        """
        Depth first search to get all topological orderings
        Parent references are treated preferentially
        """
        N = len(self.graph)
        Visited = {block_hash: False for block_hash in self.graph.keys()}
        Visited[-1] = True # Genesis block is always visited
        
        ordering = [None] * N
        i = N - 1  # Index for ordering

        for(block_hash, _) in self.graph.items():
            if not Visited[block_hash]:
                i, ordering = self.topological_sort(block_hash, Visited, ordering, i)

        return ordering
    
    def topological_sort(self, block_hash, Visited, ordering, i):
        """
        Topological sort helper function
        """
        Visited[block_hash] = True

        # Recur for all the vertices adjacent to this vertex
        for parent in [self.graph[block_hash]["parent"]]:
            if not Visited[parent]:
                i, ordering = self.topological_sort(parent, Visited, ordering, i)

        for reference in self.graph[block_hash]["references"]:
            if not Visited[reference]:
                i, ordering = self.topological_sort(reference, Visited, ordering, i)

        ordering[i] = block_hash

        return i - 1, ordering
    
    def contains_tx(self, transaction_id):
        """
        Check if a transaction is in the DAG
        """

        # Check bloomFilter first 
        if transaction_id not in self.transaction_bloomfilter:
            return False
        
        # Iterate over all blocks and check if the transaction is in there
        for _, data in self.graph.items():
            for transaction in data["block_data"].transactions:
                if transaction.id == transaction_id:
                    return True
        
        return False

class BlockDAGraphComparison:
    def get_differing_blocks(smallerGraph : BlockDAGraph, biggerGraph : BlockDAGraph):
        # Get all blocks in graph1
        blocks1 = set(smallerGraph.graph.keys())

        # Get all blocks in graph2
        blocks2 = set(biggerGraph.graph.keys())

        # Get the difference
        return blocks2 - blocks1
     
    def equal(graph1 : BlockDAGraph, graph2 : BlockDAGraph):
        # Get all blocks in graph1
        blocks1 = set(graph1.graph.keys())

        # Get all blocks in graph2
        blocks2 = set(graph2.graph.keys())

        # Get the difference
        difference = blocks2 - blocks1

        # If there is a difference, the graphs are not equal
        if len(difference) > 0:
            return False
        
        # Check references and parents
        for block_hash, data in graph1.graph.items():
            # Check parent
            if data["parent"] != graph2.graph[block_hash]["parent"]:
                return False

            # Check references
            if data["references"] != graph2.graph[block_hash]["references"]:
                return False
            
        return True