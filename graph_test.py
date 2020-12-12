import unittest
from graph import Graph

class TestGraph(unittest.TestCase):
    def test_create_graph_simple(self):
        graph = Graph()
        graph.add_edge(0, 1)
        graph.add_edge(1, 2)
        graph.add_edge(2, 0)
        graph.add_edge(2, 0) # Test double edges don't make a difference
        self.assertEqual(graph.all_vertices(), {0, 1, 2})

        self.assertCountEqual(graph.get_adjacency_list()[0], [1, 2])
        self.assertCountEqual(graph.get_adjacency_list()[1], [0, 2])
        self.assertCountEqual(graph.get_adjacency_list()[2], [0, 1])

    def test_create_graph_complex(self):
        graph = Graph()
        graph.add_edge(0, 1)
        graph.add_edge(1, 2)
        graph.add_edge(2, 3)
        graph.add_edge(2, 3)
        graph.add_edge(2, 4)
        graph.add_edge(1, 4)
        graph.add_edge(4, 5)
        graph.add_edge(5, 0)
        self.assertEqual(graph.all_vertices(), {0, 1, 2, 3, 4, 5})

        self.assertCountEqual(graph.get_adjacency_list()[0], [1, 5])
        self.assertCountEqual(graph.get_adjacency_list()[1], [0, 2, 4])
        self.assertCountEqual(graph.get_adjacency_list()[2], [1, 4, 3])
        self.assertCountEqual(graph.get_adjacency_list()[3], [2])
        self.assertCountEqual(graph.get_adjacency_list()[4], [1, 2, 5])
        self.assertCountEqual(graph.get_adjacency_list()[5], [4, 0])

    def test_remove_vertex(self):
        graph = Graph()
        graph.add_edge(0, 1)
        graph.add_edge(1, 2)
        graph.add_edge(2, 3)
        graph.add_edge(2, 3)
        graph.add_edge(2, 4)
        graph.add_edge(1, 4)
        graph.add_edge(4, 5)
        graph.add_edge(5, 0)
        self.assertEqual(graph.all_vertices(), {0, 1, 2, 3, 4, 5})

        graph.remove_vertex(0)

        self.assertEqual(graph.all_vertices(), {1, 2, 3, 4, 5})

        self.assertCountEqual(graph.get_adjacency_list()[1], [2, 4])
        self.assertCountEqual(graph.get_adjacency_list()[2], [1, 4, 3])
        self.assertCountEqual(graph.get_adjacency_list()[3], [2])
        self.assertCountEqual(graph.get_adjacency_list()[4], [1, 2, 5])
        self.assertCountEqual(graph.get_adjacency_list()[5], [4])

        graph.remove_vertex(4)

        self.assertEqual(graph.all_vertices(), {1, 2, 3, 5})

        self.assertCountEqual(graph.get_adjacency_list()[1], [2])
        self.assertCountEqual(graph.get_adjacency_list()[2], [1, 3])
        self.assertCountEqual(graph.get_adjacency_list()[3], [2])
        self.assertCountEqual(graph.get_adjacency_list()[5], [])

    def test_is_connected_with_connected_graph(self):
        graph = Graph()
        graph.add_edge(0, 1)
        graph.add_edge(1, 2)
        graph.add_edge(2, 3)
        graph.add_edge(2, 3)
        graph.add_edge(2, 4)
        graph.add_edge(1, 4)
        graph.add_edge(4, 5)
        graph.add_edge(5, 0)
        self.assertEqual(graph.all_vertices(), {0, 1, 2, 3, 4, 5})

        self.assertTrue(graph.is_connected())

    def test_is_connected_with_disconnected_graph(self):
        graph = Graph()
        graph.add_edge(0, 1)
        graph.add_edge(1, 2)
        graph.add_edge(2, 3)
        graph.add_edge(2, 3)
        graph.add_edge(2, 4)
        graph.add_edge(1, 4)
        graph.add_edge(4, 5)
        graph.add_edge(5, 0)
        self.assertEqual(graph.all_vertices(), {0, 1, 2, 3, 4, 5})

        graph.remove_vertex(2)

        self.assertFalse(graph.is_connected())

if __name__ == '__main__':
    unittest.main()

