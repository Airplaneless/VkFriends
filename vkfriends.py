import vk
import random
import argparse
import matplotlib.pylab as plt
plt.style.use('grayscale')
import networkx as nx
from multiprocessing import Pool
from networkx.drawing.nx_agraph import graphviz_layout

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

def get_name(idx):
    session = vk.Session()
    vk_api = vk.API(session, timeout=120)
    d = vk_api.users.get(user_id=idx, v=VK_API_VERSION)
    f_name = d[0]['first_name']
    l_name = d[0]['last_name']
    return '\n'.join([f_name, l_name])

def friends_graph(ID, vk_api):
    
    friends = vk_api.friends.get(user_id=ID, v=VK_API_VERSION)['items']

    graph = {}

    pool = Pool(processes=12)
    all_friends_part = pool.map(get_friends, friends)
    pool.close()

    for friend, friends_part in zip(friends, all_friends_part):
        user_friends_common = set.intersection(
            set(friends),
            set(friends_part)
        )
        graph[friend] = list(user_friends_common)

    G = nx.Graph(graph)
    nodes = G.nodes()
    mapping = {node: get_name(node) for node in nodes}
    H = nx.relabel_nodes(G, mapping)

    return H, get_name(ID)


def plot_graph(G, name):
    
    #plt.figure(figsize=(35,29))
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
    plt.show()
    #plt.savefig('{}.png'.format(name.encode('utf-8').replace('\n', '')))
    return True

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-id', type=int, help='ID of vk.com user')
    
    ID = parser.parse_args()._get_kwargs()[0][1]

    session = vk.Session()
    vk_api = vk.API(session, timeout=120)

    G, name = friends_graph(ID, vk_api)
    plot_graph(G, name)