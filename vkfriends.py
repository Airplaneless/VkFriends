import vk
import random
import argparse
import matplotlib.pylab as plt
from tqdm import tqdm
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

    pbar = tqdm(total=len(friends), desc='load names')
    pool = Pool(processes=12)
    res = pool.map_async(get_name, nodes, callback=update)
    pool.close()
    pool.join()
    pbar.close()
    names = res.get(timeout=10)
    mapping = {node: name for node, name in zip(nodes, names)}

    H = nx.relabel_nodes(G, mapping)

    return H, get_name(ID)


def plot_graph(G, name):
    
    plt.figure(figsize=(40,30))
    colors = [
        'red',
        'yellow',
        'blue',
        'green'
    ]
    edges_colors = [random.choice(colors) for _ in G.edges()]
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
    return True

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-id', type=int, help='ID of vk.com user')
    
    ID = parser.parse_args()._get_kwargs()[0][1]

    session = vk.Session()
    vk_api = vk.API(session, timeout=120)

    G, name = friends_graph(ID, vk_api)
    plot_graph(G, name)