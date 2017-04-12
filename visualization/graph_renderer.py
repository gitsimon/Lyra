from abc import abstractmethod
import graphviz as gv
import subprocess
import numbers
from uuid import uuid4 as uuid


class GraphRenderer:
    graphattrs = {
        'labelloc': 't',
        'fontcolor': 'black',
        'bgcolor': '#FFFFFF',
        'margin': '0',
    }

    nodeattrs = {
        'color': 'black',
        'fontcolor': 'black',
        'style': 'filled',
        'fillcolor': '#70a6ff',
    }

    edgeattrs = {
        'color': 'black',
        'fontcolor': 'black',
    }

    _graph = None
    _rendered_nodes = None
    _max_label_len = 100

    @staticmethod
    def _escape_dot_label(str):
        return str.replace("\\", "\\\\").replace("|", "\\|").replace("<", "\\<").replace(">", "\\>")

    def _shorten_string(self, string):
        if len(string) > self._max_label_len - 3:
            halflen = int((self._max_label_len - 3) / 2)
            return string[:halflen] + "..." + string[-halflen:]
        return string

    @abstractmethod
    def _render_graph(self, data):
        """
        Entry point for rendering graph represented by data.
        :param data: the whole data necessary to render graph
        :return:
        """

    def render(self, data, *, label=None):
        # create the graph
        graphattrs = self.graphattrs.copy()
        if label is not None:
            graphattrs['label'] = self._escape_dot_label(label)
        graph = gv.Digraph(graph_attr=graphattrs, node_attr=self.nodeattrs, edge_attr=self.edgeattrs)

        # recursively draw all the nodes and edges
        self._graph = graph
        self._rendered_nodes = set()
        self._render_graph(data)
        self._graph = None
        self._rendered_nodes = None

        # display the graph
        graph.format = "pdf"
        graph.view()
        subprocess.Popen(['xdg-open', "test.pdf"])


class ListDictTreeRenderer(GraphRenderer):
    """
    this class is capable of rendering data structures consisting of
    dicts and lists as a graph using graphviz
    """

    def _render_graph(self, data):
        self._render_node(data)

    def _render_node(self, node):
        """
        Renders a node. Recursive callee for node rendering.
        :param node: the representation of a node (dependent of rendered data structure)
        :return: node id of created node
        """
        if isinstance(node, (str, numbers.Number)) or node is None:
            node_id = uuid()
        else:
            node_id = id(node)
        node_id = str(node_id)

        if node_id not in self._rendered_nodes:
            self._rendered_nodes.add(node_id)
            if isinstance(node, dict):
                self._render_dict(node, node_id)
            elif isinstance(node, list):
                self._render_list(node, node_id)
            else:
                self._graph.node(node_id, label=self._escape_dot_label(self._shorten_string(repr(node))))

        return node_id

    def _render_dict(self, node, node_id):
        self._graph.node(node_id, label=node.get("node_type", "[dict]"))
        for key, value in node.items():
            if key == "node_type":
                continue
            child_node_id = self._render_node(value)
            self._graph.edge(node_id, child_node_id, label=self._escape_dot_label(key))

    def _render_list(self, node, node_id):
        self._graph.node(node_id, label="[list]")
        for idx, value in enumerate(node):
            child_node_id = self._render_node(value)
            self._graph.edge(node_id, child_node_id, label=self._escape_dot_label(str(idx)))


class CfgRenderer(GraphRenderer):
    """
    this class is capable of rendering a cfg
    """

    def _render_graph(self, cfg):
        for node_id, node in cfg.nodes.items():
            fillcolor = self.nodeattrs['fillcolor']
            if node is cfg.in_node:
                fillcolor = '#24bf26'
            elif node is cfg.out_node:
                fillcolor = '#ce3538'

            self._graph.node(str(node_id), label=self._escape_dot_label(self._shorten_string(repr(node))),
                             fillcolor=fillcolor)

        for edge in cfg.edges.values():
            self._graph.edge(str(edge.source.identifier), str(edge.target.identifier),
                             label=self._escape_dot_label(repr(edge)))