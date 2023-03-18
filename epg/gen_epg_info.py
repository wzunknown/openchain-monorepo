import networkx as nx
import orjson
import argparse
import urllib.request
from typing import Callable
from loguru import logger

from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.graph_traversal import GraphTraversalSource
from gremlin_python.process.graph_traversal import __ as T__
from gremlin_python.process.traversal import P, T



OPENCHAIN_TRACE_API = 'https://tx.eth.samczsun.com/api/v1/trace/ethereum/{tx}'

# https://plotly.com/python/discrete-color/
COLOR_PALETTE = ['#636efa', '#ef553b', '#00cc96', '#ab63fa', '#ffa15a', '#19d3f3', '#ff6692', '#b6e880', '#ff97ff', '#fecb52']


def match_path_callId(openchain_trace: dict, epg_graph: nx.MultiDiGraph):
    path_to_callId = {}
    callId_set = set()
    
    for _, data in epg_graph.nodes(data=True):
        if data.get('labelV') == 'contractCall':
            callId_set.add(data.get('callId'))
    
    cnt = 0
    frame = []
    def count_call(node: dict):
        nonlocal cnt, frame
        if node.get('type') != 'call':
            return
        frame_idx = node.get('path').count('.')
        if frame_idx == len(frame):
            frame.append(0)
        elif frame_idx == len(frame) - 1:
            frame[frame_idx] += 1
        else:
            frame = frame[:frame_idx + 1]
            frame[frame_idx] += 1

        cnt += 1
        callId = ':'.join(map(str, frame))
        path_to_callId[node.get('path')] = callId

        if callId not in callId_set:
            logger.warning('not found (%s, %s)' % (callId, node.get('path')))

    
    def dfs(node: dict):
        count_call(node)
        for child in node.get('children', []):
            dfs(child)
    
    dfs(openchain_trace['entrypoint'])

    callId_to_path = {v: k for k, v in path_to_callId.items()}

    return callId_to_path, path_to_callId


def get_openchain_trace(tx_hash):
    '''
    wget https://tx.eth.samczsun.com/api/v1/trace/ethereum/0x0742b138a78ad9bd5d0b55221d514637313bc64c40272ca98c8d0417a519e2e4
    '''
    with urllib.request.urlopen(OPENCHAIN_TRACE_API.format(tx=tx_hash)) as f:
        openchain_trace = orjson.loads(f.read())['result']
    
    return openchain_trace



def reentrancy_example(g: GraphTraversalSource, args):
    from epg_traverse import reentrancy_control_dependency_traverse, reentrancy_filter
    
    attacks = []
    
    for res in reentrancy_control_dependency_traverse(g):
        if reentrancy_filter(res):
            attacks.append(res)
    
    epg_graph = nx.read_graphml(args.graphml)
    openchain_trace = get_openchain_trace(args.tx)
    callId_to_path, path_to_callId = match_path_callId(openchain_trace, epg_graph)

    style = 'underline wavy {color}'
    highlight = {'nodes': {}, 'slots': {}}
    for idx, atk in enumerate(attacks):
        nodes = []
        slots = []
        dcfgId = atk['victim_flow_dcfg']['dcfgId']
        victim_flow_callId = dcfgId.split('-')[0] + ':' + dcfgId.split('-')[-1]
        nodes += [victim_flow_callId, atk['victim']['callId'], atk['reentry']['callId']]
        nodes = [callId_to_path[v] for v in nodes]

        state_slot = atk['state_change']['sourceLocation'].split(':')[1]
        state_change_callId = atk['state_change_dcfg']['dcfgId'].split('-')[0]
        state_change_path = callId_to_path[state_change_callId]
        nodes.append(state_change_path)
        
        curr_node = openchain_trace['entrypoint']
        for idx_str in state_change_path.split('.')[1:]:
            curr_node = curr_node['children'][int(idx_str)]
        
        for child in curr_node['children']:
            if child['type'] in ['sload', 'sstore'] and child['slot'] == state_slot:
                slots.append(child['path'])
        
        highlight['nodes'].update({x: style.format(color=COLOR_PALETTE[idx % len(COLOR_PALETTE)]) for x in nodes})
        highlight['slots'].update({x: style.format(color=COLOR_PALETTE[idx % len(COLOR_PALETTE)]) for x in slots})
    
    logger.info(f'output to {args.output_dir}/map.json and {args.output_dir}/highlight.json')
    with open('%s/map.json' % (args.output_dir,), 'wb') as f:
        f.write(orjson.dumps(path_to_callId))
    with open('%s/highlight.json' % (args.output_dir,), 'wb') as f:
        f.write(orjson.dumps(highlight))


    
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--graphml', required=True,
                        help='exported graphml (xml) of epg')
    parser.add_argument('-t', '--tx', required=True,
                        help='target transaction hash')
    parser.add_argument('-r', '--gremlin-url', required=True,
                        help='gremlin server for traverse query')
    parser.add_argument('-o', '--output-dir', required=True,
                        help='output info json files')
    
    args = parser.parse_args()
    
    g = traversal().withRemote(DriverRemoteConnection(args.gremlin_url,'g'))
    
    #====== reentrancy example =======
    reentrancy_example(g, args)
    # python3 epg/gen_epg_info.py --gremlin-url ws://172.17.0.10:8182/gremlin --tx 0x0742b138a78ad9bd5d0b55221d514637313bc64c40272ca98c8d0417a519e2e4 --graphml /exported-graphs/0x0742b138a78ad9bd5d0b55221d514637313bc64c40272ca98c8d0417a519e2e4.xml -o frontend/tmp
    
    
    
    