from graph import Graph
from bounding_box import BoundingBox, Point
from util import *
from collections import deque

class Node():
    def __init__(self, solid):
        assert isinstance(solid, TopoDS_Solid)
        self._solid = copy.deepcopy(solid)
        props = GlobalProperties(solid)
        x1, y1, z1, x2, y2, z2 = props.bbox()
        xmin = min(x1, x2)
        xmax = max(x1, x2)
        ymin = min(y1, y2)
        ymax = max(y1, y2)
        zmin = min(z1, z2)
        zmax = max(z1, z2)
        self._bbox = BoundingBox(xmin, ymin, zmin, xmax, ymax, zmax)

    def solid(self):
        return self._solid

    def bbox(self):
        return self._bbox

def create_solid_graph(solids):
    graph = Graph()
    if not solids:
        return graph

    def _is_adjacent(node1, node2):
        assert isinstance(node1, Node)
        assert isinstance(node2, Node)

        overlap = node1.bbox().overlaps(node2.bbox())
        close = node1.bbox().dist(node2.bbox()) < 0.1
        return overlap and close

    nodes = {Node(s) for s in solids}
    visited = set()
    frontier = deque()
    frontier.append(nodes.pop())
    while frontier:
        node = frontier.pop()
        visited.add(node)
        adjacent = [n for n in nodes if n not in visited and _is_adjacent(node, n)]
        for a in adjacent:
            graph.add_edge(node, a)
            frontier.append(a)

    assert len(graph.all_vertices()) == len(solids)
    assert graph.is_connected()

    return graph


def remove_redundant_geom(compound):
    all_solids = split_compound(compound)
    graph = create_solid_graph(all_solids)

    props = GlobalProperties(compound)
    x1, y1, z1, x2, y2, z2 = props.bbox()

    corner = Point(x2, y1, z2)
    vertices = graph.all_vertices()
    vertices.sort(key=lambda x: x.bbox().max_dist_to_point(corner))

    return vertices



