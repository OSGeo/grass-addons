#!/usr/bin/env python

############################################################################
#
# MODULE:       v.stream.order
# AUTHOR(S):    IGB-Berlin,Johannes Radinger; Implementation: Geoinformatikbuero Dassau GmbH , Soeren Gebbert
#
#               This tool was developed as part of the BiodivERsA-net project 'FISHCON'
#               and has been funded by the German Federal Ministry for Education and
#               Research (grant number 01LC1205).
#
# PURPOSE:      Compute the stream order of stream networks stored in
#               a vector map at specific outlet vector points
# COPYRIGHT:    (C) 2015 by the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

# %module
# % description: Compute the stream order of stream networks stored in a vector map at specific outlet vector points
# % keyword: vector
# % keyword: hydrology
# % keyword: stream network
# % keyword: stream order
# %end
# %option G_OPT_V_INPUT
# % description: Name of the stream networks vector map
# %end
# %option G_OPT_V_INPUT
# % key: points
# % label: Name of the input vector point map
# % description: Name of the points vector map that defines the water outlets of the stream networks
# %end
# %option G_OPT_V_OUTPUT
# % label: Name of the vector output map
# % description: The name for the stream order vector output map
# %end
# %option
# % key: threshold
# % type: double
# % description: threshold in projection units used to search for outflow points at the stream network
# % required : no
# % answer: 25
# % multiple: no
# %end
# %option
# % key: order
# % type: string
# % description: The stream order to compute
# % required : no
# % answer: strahler,shreve
# % options: strahler,shreve,scheidegger,drwal
# % multiple: yes
# %end
# %option
# % key: columns
# % type: string
# % description: The columns that should be copied from the input stream vector map. By default all will be copied.
# % answer: all
# % required : no
# % multiple: yes
# %end
# %option
# % key: recursionlimit
# % type: integer
# % description:The Python recursion limit that should be used (Python default is 1000)
# % required : no
# % answer: 10000
# % multiple: no
# %end

import os
import sys
from grass.script import core as grass
from grass.pygrass.vector import VectorTopo
import math

# for Python 3 compatibility
try:
    xrange
except NameError:
    xrange = range

ORDER_STRAHLER = 1
ORDER_SHREVE = 2
ORDER_SCHEIDEGGER = 3
ORDER_DRWAL = 4
ORDER_HORTON = 5

ORDER_DICT = {
    ORDER_STRAHLER: "strahler",
    ORDER_SHREVE: "shreve",
    ORDER_SCHEIDEGGER: "scheidegger",
    ORDER_DRWAL: "drwal",
    ORDER_HORTON: "horton",
}


class GraphEdge(object):
    """
    This class defines a single edge of the stream network graph
    """

    def __init__(self, id_, id_pol, start, end, start_edges, end_edges, reverse=False):
        self.id = id_  # Line id
        self.id_pol = id_pol  # Polarity of line positive integer or negative integer
        self.start = start  # Start Node id
        self.end = end  # End Node id
        self.start_edges = start_edges  # A list of edge ids at the start node
        self.end_edges = end_edges  # A list of edge ids at the end node
        self.reverse = reverse  # If the edge should be reversed
        self.stream_order = {
            ORDER_STRAHLER: 0,
            ORDER_SHREVE: 0,
            ORDER_SCHEIDEGGER: 0,
            ORDER_DRWAL: 0,
        }  # stream_order for each algorithm

    def __str__(self):
        return (
            "Line id: %i (%i) start node: %i "
            "end node: %i num start edges %i "
            "num end edges %i   reverse: %s stream_order: %s"
            % (
                self.id,
                self.id_pol,
                self.start,
                self.end,
                len(self.start_edges),
                len(self.end_edges),
                self.reverse,
                str(self.stream_order),
            )
        )


class GraphNode(object):
    """
    This class defines a single node of the node network graph
    """

    def __init__(self, id_, edge_ids):
        self.id = id_  # Node id
        self.edge_ids = edge_ids  # Line ids

    def __str__(self):
        return "Node id: %i line ids: %s" % (self.id, self.edge_ids)


def traverse_graph_create_stream_order(
    start_id,
    edges,
    checked_edges,
    reversed_edges,
    order_types=[ORDER_STRAHLER, ORDER_SHREVE],
):
    """
    Traverse the graph, reverse lines that are not in
    the outflow direction and compute the required orders

    :param start_id: The id of the edge to start the traversing from
    :param edges: A dictionary of edge objects
    :param checked_edges: A list with edge ids that have been checked already
    :param reversed_edges: A list of edges that have been checked for
                           reversion and corrected if necessary
    :param order_types: The type of the ordering scheme as a list of ints
                      * ORDER_STRAHLER = 1
                      * ORDER_SHREVE = 2
                      * ORDER_SCHEIDEGGER = 3
                      * ORDER_DRWAL = 4
                      * ORDER_HORTON = 5 -> Not correct implemented

    :return:
    """
    current_edge = edges[start_id]

    # Check for direction reversion
    for edge_id in current_edge.start_edges:
        if edge_id not in reversed_edges:
            reversed_edges.append(edge_id)
            edge = edges[edge_id]

            # Reverse the edge if it is not in the outflow direction
            if current_edge.start != edge.end:
                start = edge.start
                start_edges = edge.start_edges
                edge.start = edge.end
                edge.start_edges = edge.end_edges
                edge.end = start
                edge.end_edges = start_edges
                edge.reverse = True

    # Set the stream_order to one, if the edge is a leaf and return
    if len(current_edge.start_edges) == 0:
        for order in current_edge.stream_order:
            current_edge.stream_order[order] = 1
        return

    stream_orders = {
        ORDER_STRAHLER: [],
        ORDER_SHREVE: [],
        ORDER_SCHEIDEGGER: [],
        ORDER_HORTON: [],
        ORDER_DRWAL: [],
    }

    # Traverse the graph if its not a leaf
    for edge_id in current_edge.start_edges:
        if edge_id not in checked_edges:
            checked_edges.append(edge_id)
            traverse_graph_create_stream_order(
                edge_id, edges, checked_edges, reversed_edges, order_types
            )

        for order in order_types:
            stream_orders[order].append(edges[edge_id].stream_order[order])

    # Compute the stream orders
    if ORDER_STRAHLER in order_types:
        maximum = max(stream_orders[ORDER_STRAHLER])
        if stream_orders[ORDER_STRAHLER].count(maximum) > 1:
            current_edge.stream_order[ORDER_STRAHLER] = maximum + 1
        else:
            current_edge.stream_order[ORDER_STRAHLER] = maximum
    if ORDER_SHREVE in order_types:
        current_edge.stream_order[ORDER_SHREVE] = sum(stream_orders[ORDER_SHREVE])
    if ORDER_SCHEIDEGGER in order_types:
        current_edge.stream_order[ORDER_SCHEIDEGGER] = sum(
            stream_orders[ORDER_SCHEIDEGGER]
        )
    if ORDER_DRWAL in order_types:
        current_edge.stream_order[ORDER_DRWAL] = sum(stream_orders[ORDER_DRWAL])
    # Horton is wrong implemented
    if ORDER_HORTON in order_types:
        maximum = max(stream_orders[ORDER_HORTON])
        current_edge.stream_order[ORDER_HORTON] = maximum + 1


def traverse_network_create_graph(vector, start_node, graph_nodes, graph_edges):
    """
    Traverse a stream network vector map layer with depth-first search
    and create a graphs structures for nodes and edges

    :param vector: The opened vector input file
    :param start_node: The start node object
    :param graph_nodes: A dictionary of discovered nodes
    :param graph_edges: A dictionary of Edge objects
    :return:
    """

    # Count line ids
    edge_ids = start_node.ilines()

    # For each line at that node
    for line_id in edge_ids:

        line_id_abs = abs(line_id)
        line = vector.read(line_id_abs)
        nodes = line.nodes()

        # If the line id is not in the edge list, create a new entry
        if line_id_abs not in graph_edges:
            start_edges = [abs(lid) for lid in nodes[0].ilines()]
            end_edges = [abs(lid) for lid in nodes[1].ilines()]

            start_edges.remove(line_id_abs)
            end_edges.remove(line_id_abs)

            e = GraphEdge(
                line_id_abs,
                line_id,
                nodes[0].id,
                nodes[1].id,
                start_edges,
                end_edges,
                False,
            )
            graph_edges[line_id_abs] = e

        # For start and end node
        for node in nodes:
            # If the node was not yet discovered, put it
            # into the node dict and call traverse
            if node.id not in graph_nodes:
                graph_nodes[node.id] = GraphNode(
                    node.id, [lid for lid in node.ilines()]
                )
                # Recursive call
                traverse_network_create_graph(vector, node, graph_nodes, graph_edges)


def graph_to_vector(
    name, mapset, graphs, output, order_types, outlet_cats, copy_columns
):
    """
    Write the Graph as vector map. Attach the network id,
    the streams orders, the reverse falg, the original
    category and copy columns from the source stream network
    vector map if required.

    :param name: Name of the input stream vector map
    :param mapset: Mapset name of the input stream vector map
    :param graphs: The list of computed graphs
    :param output: The name of the output vector map
    :param order_types: The order algorithms
    :param outlet_cats: Categories of the outlet points
    :param copy_columns: The column names to be copied from the original input map
    :return:
    """
    streams = VectorTopo(name=name, mapset=mapset)
    streams.open("r")

    # Specifiy all columns that should be created
    cols = [
        ("cat", "INTEGER PRIMARY KEY"),
        ("outlet_cat", "INTEGER"),
        ("network", "INTEGER"),
        ("reversed", "INTEGER"),
    ]

    for order in order_types:
        cols.append((ORDER_DICT[order], "INTEGER"))

    # Add the columns of the table from the input map
    if copy_columns:
        for entry in copy_columns:
            cols.append((entry[1], entry[2]))

    out_streams = VectorTopo(output)
    grass.message(_("Writing vector map <%s>" % output))
    out_streams.open("w", tab_cols=cols)

    count = 0
    for graph in graphs:
        outlet_cat = outlet_cats[count]
        count += 1

        grass.message(
            _(
                "Writing network %i from %i with "
                "outlet category %i" % (count, len(graphs), outlet_cat)
            )
        )

        # Write each edge as line
        for edge_id in graph:
            edge = graph[edge_id]

            line = streams.read(edge_id)
            # Reverse the line if required
            if edge.reverse is True:
                line.reverse()

            # Orders derived from shreve algorithm
            if ORDER_SCHEIDEGGER in order_types:
                edge.stream_order[ORDER_SCHEIDEGGER] *= 2
            if ORDER_DRWAL in order_types:
                if edge.stream_order[ORDER_DRWAL] != 0:
                    edge.stream_order[ORDER_DRWAL] = int(
                        math.log(edge.stream_order[ORDER_DRWAL], 2) + 1
                    )

            # Create attributes
            attrs = []
            # Append the outlet point category
            attrs.append(outlet_cat)
            # Append the network id
            attrs.append(count)
            # The reverse flag
            attrs.append(edge.reverse)
            # Then the stream orders defined at the command line
            for order in order_types:
                val = int(edge.stream_order[order])
                if val == 0:
                    val = None
                attrs.append(val)
            # Copy attributes from original streams if the table exists
            if copy_columns:
                for entry in copy_columns:
                    # First entry is the column index
                    attrs.append(line.attrs.values()[entry[0]])

            # Write the feature
            out_streams.write(line, cat=edge_id, attrs=attrs)

    # Commit the database entries
    out_streams.table.conn.commit()
    # Close the input and output map
    out_streams.close()
    streams.close()


def detect_compute_networks(
    vname, vmapset, pname, pmapset, output, order, columns, threshold
):
    """
    Detect the start edges and nodes, compute the stream networks
    and stream orders, reverse edges and write everything into the
    output vector map.

    :param vname: Name of the input stream vector map
    :param vmapset: Mapset name of the input stream vector map
    :param pname: Name of the input outlet points vector map
    :param pmapset: Mapset name of the input outlet points vector map
    :param output: Name of the output stream vector map
    :param order: Comma separated list of order algorithms
    :param columns: Comma separated list of column names that should be copied to the output
    :param threshold: The point search threshold to find start edges and nodes
    :return:
    """

    v = VectorTopo(name=vname, mapset=vmapset)
    p = VectorTopo(name=pname, mapset=pmapset)

    v.open(mode="r")
    p.open(mode="r")

    copy_columns = None

    # Check for copy columns only if the input vector map
    # has an attribute table
    if v.table and columns:

        # These are the column names that are newly created
        # and it must be checked if their names
        # are exist in the input map column names
        # that should be copied
        # Synchronize these names with the graph_to_vector() function
        new_column_names = order.split(",")
        new_column_names.append("cat")
        new_column_names.append("outlet_cat")
        new_column_names.append("network")
        new_column_names.append("reversed")
        # Add the order colum names
        new_column_names.extend(order)

        # Check if all columns should be copied
        if columns.lower() == "all":
            columns = ",".join(v.table.columns.names())

        copy_columns = []
        for column in columns.split(","):
            # Copy only columns that exists
            if column in v.table.columns.names():
                col_index = v.table.columns.names().index(column)
                col_type = v.table.columns.types()[col_index]
                # Rename the column if it conflicts with the
                # order column names in the output map
                if column in new_column_names:

                    # Create name suffix and make sure that the new column name
                    # does not exists
                    number = 1
                    suffix = ""
                    while True:
                        suffix = "_%i" % number
                        if (
                            column + suffix not in new_column_names
                            and column + suffix not in columns.split(",")
                        ):
                            break
                        number += 1

                    grass.warning(
                        _(
                            "Column name conflict: Renaming column "
                            "<%(col)s> from input map into %(col)s%(ap)s "
                            "in output map" % {"col": column, "ap": suffix}
                        )
                    )
                    column += suffix
                copy_columns.append((col_index, column, col_type))
            else:
                v.close()
                p.close()
                grass.fatal(
                    _("Column %s is not in attribute table of <%s>" % (column, vname))
                )

    # Detect closest edges and nodes to the outflow points
    # But why nodes, arent edges sufficient?
    #     They may be useful when detecting loops and channels
    #     in further improvements of v.stream.order.
    start_nodes = []
    start_node_ids = []
    start_edges = []
    outlet_cats = []

    for point in p:
        p_coords = point.coords()

        line = v.find_by_point.geo(point=point, maxdist=float(threshold), type="line")

        if line:
            n1, n2 = line.nodes()

            n1_coords = n1.coords()
            n2_coords = n2.coords()

            # Compute closest node to the outflow point
            dist1 = math.sqrt(
                (p_coords[0] - n1_coords[0]) ** 2 + (p_coords[1] - n1_coords[1]) ** 2
            )
            dist2 = math.sqrt(
                (p_coords[0] - n2_coords[0]) ** 2 + (p_coords[1] - n2_coords[1]) ** 2
            )

            if dist1 < dist2:
                closest_node = n1
            else:
                closest_node = n2

            grass.verbose(
                _("Detect edge <%i> for outflow point %s" % (line.id, point.to_wkt()))
            )

            # Ignore identical starting points to avoid
            # redundant networks in the output
            if closest_node.id not in start_node_ids:
                start_nodes.append(closest_node)
                start_node_ids.append(closest_node.id)

            if line.id not in start_edges:
                start_edges.append(line.id)
                outlet_cats.append(point.cat)
            else:
                grass.warning(_("Ignoring duplicated start edge"))

    p.close()

    if len(start_edges) == 0:
        v.close()
        grass.fatal(_("Unable to find start edges"))

    if len(start_nodes) == 0:
        v.close()
        grass.fatal(_("Unable to find start nodes"))

    # We create a graph representation for further computations
    graphs = []

    # Traverse each network from the outflow node on
    for node in start_nodes:
        graph_nodes = {}
        graph_edges = {}
        graph_nodes[node.id] = GraphNode(node.id, [lid for lid in node.ilines()])
        traverse_network_create_graph(v, node, graph_nodes, graph_edges)
        # For now we only use the edges graph
        graphs.append(graph_edges)

    # Close the vector map, since we have our own graph representation
    v.close()

    # Set stream order types
    order_types = []

    if order.find("strahler") >= 0:
        order_types.append(ORDER_STRAHLER)
    if order.find("scheidegger") >= 0:
        order_types.append(ORDER_SCHEIDEGGER)
    if order.find("drwal") >= 0:
        order_types.append(ORDER_DRWAL)
    if order.find("horton") >= 0:
        order_types.append(ORDER_HORTON)
    if order.find("shreve") >= 0:
        order_types.append(ORDER_SHREVE)

    # Compute the stream orders
    for i in xrange(len(start_edges)):
        edge_id = start_edges[i]
        checked_edges = []
        reversed_edges = []
        traverse_graph_create_stream_order(
            edge_id, graphs[i], checked_edges, reversed_edges, order_types
        )

    # Write the graphs as vector map
    graph_to_vector(
        vname, vmapset, graphs, output, order_types, outlet_cats, copy_columns
    )


def main():
    input = options["input"]
    points = options["points"]
    output = options["output"]
    order = options["order"]
    threshold = options["threshold"]
    columns = options["columns"]
    recursionlimit = options["recursionlimit"]

    # We are using a recursive tree traversing algorithm, that may exceed
    # the 1000 recursion length for huge networks.
    # The default is 10000 in the option section
    if int(recursionlimit) < 1000:
        grass.fatal(_("The Python recursion limit should be equal or larger than 1000"))

    sys.setrecursionlimit(int(recursionlimit))

    # Check map names for mapsets
    vname = input
    vmapset = ""
    if "@" in input:
        vname, vmapset = input.split("@")

    pname = points
    pmapset = ""
    if "@" in points:
        pname, pmapset = points.split("@")

    detect_compute_networks(
        vname, vmapset, pname, pmapset, output, order, columns, threshold
    )


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
