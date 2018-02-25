import vk
import random
import argparse
import matplotlib.pylab as plt
import networkx as nx
from multiprocessing import Pool
from networkx.drawing.nx_agraph import graphviz_layout


def friends_graph(ID):
    
    session = vk.Session()
    vk_api = vk.API(session, timeout=120)

    def get_name(idx):
        d = vk_api.users.get(user_id=idx)
        f_name = d[0]['first_name']
        l_name = d[0]['last_name']
        return '\n'.join([f_name, l_name])

    def is_deleted(idx):
        d = vk_api.users.get(user_id=idx)
        if 'deactivated' in d[0]:
            return True
        else:
            return False

    friends = vk_api.friends.get(user_id=ID)

    graph = {}
    for user in friends:
        if not is_deleted(user):
            user_friends = vk_api.friends.get(user_id=user)
            user_friends_common = set.intersection(
                set(friends),
                set(user_friends)
            )
            graph[user] = list(user_friends_common)

    G = nx.Graph(graph)
    nodes = G.nodes()
    mapping = {node: get_name(node) for node in nodes}
    H = nx.relabel_nodes(G, mapping)

    return H, get_name(ID)


def plot_graph(G, name):
    
    plt.figure(figsize=(35,29))
    colors = [
        'red',
        'yellow',
        'blue',
        'green'
    ]
    edges_colors = [random.choice(colors) for e in G.edges()]
    nx.draw_networkx(
        G,
        pos=graphviz_layout(G),
        edge_color=edges_colors, 
        node_size=50, 
        font_size=8,
        node_color='green'
    )
    plt.title('Relationship of friends', size=40)
    plt.axis('off')
    plt.savefig('{}.png'.format(name.encode('utf-8').replace('\n', '')))
    return True

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--ids', nargs='+', type=int)

    IDs = parser.parse_args()._get_kwargs()[0][1]

    def plot(ID):
        G, name = friends_graph(ID)
        plot_graph(G, name)
        print '{} complete'.format(ID)

    pool = Pool(processes=len(IDs))
    pool.map(plot, IDs)
    pool.close()
