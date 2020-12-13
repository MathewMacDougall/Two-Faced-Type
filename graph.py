from collections import defaultdict
import copy
from collections import deque

class Graph:
    """
    Simple undirected graph represented with adjacency list
    """

    def __init__(self):
        self.graph = defaultdict(list)

    def add_node(self, v):
        if v not in self.graph.keys():
            self.graph[v] = []

    def add_edge(self, v1, v2):
        if v2 not in self.graph[v1]:
            self.graph[v1].append(v2)
        if v1 not in self.graph[v2]:
            self.graph[v2].append(v1)

    def remove_vertex(self, v):
        foo = self.graph.pop(v, None)
        # if foo is None:
        #     print("ERROR. Didn't find vertex to remove")
        for vertex, adjacency in self.graph.items():
            try:
                adjacency.remove(v)
            except ValueError:
                pass

    def all_vertices(self):
        return {k for k in self.graph.keys()}

    def get_adjacency_list(self):
        return copy.deepcopy(self.graph)

    def is_connected(self):
        if not self.graph.keys():
            return True

        visited = set()
        frontier = deque()
        frontier.append(list(self.graph.keys())[0])

        while frontier:
            vertex = frontier.pop()
            visited.add(vertex)
            for adj in self.graph[vertex]:
                if adj not in visited:
                    frontier.append(adj)

        num_visited = len(visited)
        num_nodes = len(self.graph.keys())
        return num_visited == num_nodes

    def get_adjacent(self, node):
        if self.node_exists(node):
            return self.graph[node]
        else:
            return []

    def node_exists(self, node):
        return node in self.graph

    def bfs(self, node, depth=0, visited=None):
        if visited is None:
            visited = set()
        if depth==0:
            # return [a for a in self.graph[node] if a not in visited]
            return [node]

        result = []
        for a in [n for n in self.graph[node] if n not in visited]:
            visited.add(a)
            result += self.bfs(a, depth-1, visited)
        return result

