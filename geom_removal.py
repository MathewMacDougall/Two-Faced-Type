from OCC.Core.BRep import BRep_Builder

from OCCUtils.base import BaseObject
from OCCUtils.Common import to_string
from OCCUtils.solid import Solid
from graph import Graph
from bounding_box import BoundingBox, Point
from util import *
from collections import deque
from solid_face_validator import SolidFaceValidator
from OCCUtils.Construct import compound as make_compound

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

    def __hash__(self):
        return self._bbox.__hash__()
        # return self._solid.__hash__() + self._bbox.__hash__()

    def __eq__(self, other):
        bbox_eq = self._bbox == other.bbox()
        return bbox_eq
        # Ignore the shapes for now. The equality is based on memory location, so doesn't work
        # and i haven't found another way to check for geometry equality yet. In theory the bbox
        # should be enough anyway for this use case

    def __ne__(self, other):
        return not self.__eq__(other)

def create_solid_graph(solids):
    graph = Graph()
    if not solids:
        return graph

    def _is_adjacent(node1, node2):
        assert isinstance(node1, Node)
        assert isinstance(node2, Node)

        overlap = node1.bbox().overlaps(node2.bbox(), threshold=1)
        close = node1.bbox().dist(node2.bbox()) < 0.1
        return overlap and close

    nodes = {Node(s) for s in solids}
    visited = set()
    frontier = deque()
    frontier.append(nodes.pop())
    while frontier:
        node = frontier.pop()
        visited.add(node)
        graph.add_node(node)
        adjacent = [n for n in nodes if n not in visited and _is_adjacent(node, n)]
        for a in adjacent:
            graph.add_edge(node, a)
            frontier.append(a)

    assert len(graph.all_vertices()) == len(solids)
    assert graph.is_connected()

    return graph

def create_compound(nodes):
    aRes = TopoDS_Compound()
    aBuilder = BRep_Builder()
    aBuilder.MakeCompound(aRes)
    for n in nodes:
        aBuilder.Add(aRes, n.solid())
    return aRes

def remove_redundant_geom(compound):
    validator = SolidFaceValidator(compound)
    all_solids = split_compound(compound)
    graph = create_solid_graph(all_solids)

    props = GlobalProperties(compound)
    x1, y1, z1, x2, y2, z2 = props.bbox()
    corner = Point(x2, y1, z2)
    vertices_to_remove = list(graph.all_vertices())
    vertices_to_remove.sort(key=lambda x: x.bbox().max_dist_to_point(corner), reverse=True)

    for index, v in enumerate(vertices_to_remove):
        new_graph = copy.deepcopy(graph)
        new_graph.remove_vertex(v)
        new_compound = create_compound(new_graph.all_vertices())
        faces_valid = validator.is_valid(new_compound)
        is_connected = new_graph.is_connected()

        if faces_valid and is_connected:
            graph = copy.deepcopy(new_graph)

    final_geom = create_compound(graph.all_vertices())

    return final_geom


def remove_redundant_geometry(shapes):
    return [remove_redundant_geom(shape) for shape in shapes]
