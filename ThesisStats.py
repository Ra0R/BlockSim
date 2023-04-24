

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from RecordedBlock import MempoolOfNode


class ThesisStats:

    def jaccard_similarity(self, a, b):
        # calculate the Jaccard similarity coefficient
        set1 = set(a)
        set2 = set(b)
        jaccard_sim = len(set1.intersection(set2)) / len(set1.union(set2))
        return jaccard_sim
    
    def mempool_similarity_matrix(self, mempoolsOfNode  : list[MempoolOfNode]) -> list[list[float]]:
        # calculate the similarity matrix for the mempools
        similarity_matrix = []
        for i in range(len(mempoolsOfNode)):
            similarity_matrix.append([])
            for j in range(len(mempoolsOfNode)):
                mempool1 = mempoolsOfNode[i].mempool
                mempool2 = mempoolsOfNode[j].mempool

                # Convert mempool to list of hashes
                mempool1 = [tx.hash for tx in mempool1]
                mempool2 = [tx.hash for tx in mempool2]

                similarity_matrix[i].append(self.jaccard_similarity(mempool1, mempool2))

        return similarity_matrix

    def plot_mempool_similarity_matrix(self, mempool_similarity_matrix: list[list[float]]):
        import numpy as np

        sns.set_theme(style="white")

        mask = np.triu(np.ones_like(mempool_similarity_matrix, dtype=np.bool))

        # Add identity to the mask
        for i in range(len(mempool_similarity_matrix)):
            mask[i][i] = False

        f, ax = plt.subplots(figsize=(11, 9))

        cmap = sns.diverging_palette(230, 20, as_cmap=True)
        # Add name of plot 
        plt.title("Mempool similarity matrix")


        sns.heatmap(mempool_similarity_matrix, mask=mask, cmap=cmap,vmin=0,vmax=0.5, center=0,
                    square=True, linewidths=.5, cbar_kws={"shrink": .5}, annot=True,
                    xticklabels=[f"Node {i}" for i in range(len(mempool_similarity_matrix))],
                    yticklabels=[f"Node {i}" for i in range(len(mempool_similarity_matrix))])

        # plt.draw()
        # plt.pause(0.01)

        return plt