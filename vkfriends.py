#!/usr/bin/env python
# -*- coding: utf-8 -*-
import vk
import random
import argparse
import pylab as plt
from tqdm import tqdm
plt.style.use('grayscale')
import networkx as nx
import json
from bokeh.io import show, output_file
from bokeh.plotting import figure
from bokeh.models import Plot, Range1d, MultiLine, Circle, HoverTool, TapTool
from bokeh.models import ColumnDataSource, BoxSelectTool, PanTool, WheelZoomTool, LabelSet
from bokeh.models.graphs import from_networkx, NodesAndLinkedEdges, EdgesAndLinkedNodes
from bokeh.palettes import Spectral4
from networkx.readwrite import json_graph
from multiprocessing import Pool
from networkx.drawing.nx_agraph import graphviz_layout

import sys
reload(sys)
sys.setdefaultencoding('utf8')

VK_API_VERSION = 5.73


def get_friends(user):
    session = vk.Session()
    vk_api = vk.API(session, timeout=120)
    deleted = vk_api.users.get(user_id=user, v=VK_API_VERSION)
    if not 'deactivated' in deleted[0]:
        user_friends = vk_api.friends.get(user_id=user, v=VK_API_VERSION)['items']
        return user_friends
    else:
        return []

def get_name_n_photo(idx):
    session = vk.Session()
    vk_api = vk.API(session, timeout=120)
    d = vk_api.users.get(user_id=idx, fields=['photo_50'], v=VK_API_VERSION)
    f_name = d[0]['first_name']
    l_name = d[0]['last_name']
    return ['\n'.join([f_name, l_name]), d[0]['photo_50']]


def friends_graph(ID, vk_api):
    
    friends = vk_api.friends.get(user_id=ID, v=VK_API_VERSION)['items']
    graph = {}

    pbar = tqdm(total=len(friends), desc='get common friends')

    def update(*a):
        pbar.update(len(friends))

    pool = Pool(processes=12)
    res = pool.map_async(get_friends, friends, callback=update)
    pool.close()
    pool.join()
    pbar.close()
    all_friends_part = res.get(timeout=10)

    for friend, friends_part in tqdm(zip(friends, all_friends_part), desc='building graph'):
        user_friends_common = set.intersection(
            set(friends),
            set(friends_part)
        )
        graph[friend] = list(user_friends_common)

    G = nx.Graph(graph)
    nodes = G.nodes()

    pbar = tqdm(total=len(friends), desc='load names and photos')
    pool = Pool(processes=12)
    res = pool.map_async(get_name_n_photo, nodes, callback=update)
    pool.close()
    pool.join()
    pbar.close()
    names_n_photos = res.get(timeout=10)
    names = [a[0] for a in names_n_photos]
    photos = {name:a[1] for name, a in zip(names, names_n_photos)}
    mapping = {node: name for node, name in zip(nodes, names)}
    
    H = nx.relabel_nodes(G, mapping)



    return H, photos, get_name_n_photo(ID)[0]


def plot_graph(G, photos, user_name):
    
    colors = [
        'red',
        'yellow',
        'blue',
        'green'
    ]
    edges_colors = [random.choice(colors) for _ in G.edges()]

    pos = graphviz_layout(G)
    names = pos.keys()
    x,y=zip(*pos.values())

    x_edge = list()
    y_edge = list()
    for edge in G.edges().keys():
        x_edge.append(pos[edge[0]][0])
        x_edge.append(pos[edge[1]][0])
        y_edge.append(pos[edge[0]][1])
        y_edge.append(pos[edge[1]][1])
    img = [photos[name] for name in names]

    edge_names = [' ' for _ in G.edges().keys()]
    
    plot = figure(plot_width=1000, plot_height=600, title="Relationship of {}".format(user_name))
    source_nodes = ColumnDataSource(data=dict(x=x, y=y, name=names, img=img))
    source_edges = ColumnDataSource(data=dict(x=x_edge, y=y_edge))
    labels = LabelSet(x='x', y='y', text='name', source=source_nodes)

    hover = HoverTool( names=['nodes'], tooltips="""
        <div>
            <div>
                <img
                    src="@img" height="42" alt="@img" width="42"
                    style="float: left; margin: 0px 15px 15px 0px;"
                    border="2"
                ></img>
            </div>
            <div>
                <span style="font-size: 10px; color: #696;">@name</span>
            </div>
        </div>
        """
    )

    plot.add_tools(hover, TapTool(), BoxSelectTool())
    plot.line('x', 'y', line_alpha=0.8, line_color="#CCCCCC", line_width=1, source=source_edges)
    plot.circle('x', 'y', size=15, fill_color=Spectral4[2], name="nodes",  source=source_nodes)
    plot.renderers.append(labels)

    output_file("networkx_graph.html")
    show(plot)

    return True

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-id', type=int, help='ID of vk.com user')
    
    identificator = parser.parse_args()._get_kwargs()[0][1]

    session = vk.Session()
    vk_api = vk.API(session, timeout=120)

    G, photos, name = friends_graph(identificator, vk_api)
    plot_graph(G, photos, name)
    