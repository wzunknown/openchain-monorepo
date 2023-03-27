from loguru import logger

from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.graph_traversal import GraphTraversalSource
from gremlin_python.process.graph_traversal import __ as T__
from gremlin_python.process.traversal import P, T

from epg_graph import DcfgId


def reentrancy_control_dependency_traverse(g: GraphTraversalSource):
    return (
        g.V().hasLabel('contractCall').as_('attacker')
            .repeat(T__.out('call')).emit().as_('victim')
            .where('attacker', P.neq('victim')).by('address')
            .repeat(T__.out('call')).emit().as_('re_attacker')
            .where('attacker', P.eq('re_attacker')).by('address')
            .repeat(T__.out('call')).emit().as_('re_victim')
            .where('victim', P.eq('re_victim')).by('address')
            .local(
                T__
                .emit().repeat(T__.out('call'))
                .out('transfer').as_('victim_flow')
                .in_('dcfg_to_asset_flow').dedup().as_('victim_flow_dcfg')
                .emit().repeat(T__.in_('jump'))
                .in_('dataflow:control')
                .emit().repeat(T__.in_('dataflow:dependency')).dedup()
                .has('sourceType', 'Storage')
                .repeat(T__.out('dataflow:transition')).emit().as_('state_change')
                .in_('dataflow:write').as_('state_change_dcfg').dedup()
                .where(
                    T__
                    .repeat(T__.in_('jump')).emit()
                    .hasLabel('contractCall')
                    .emit().repeat(T__.in_('call'))
                    .where(P.eq('victim')).count().is_(P.gt(0))
                )
                .select('attacker', 're_attacker', 'victim', 're_victim', 'state_change', 'state_change_dcfg', 'victim_flow', 'victim_flow_dcfg').by(T__.elementMap()).dedup()
            )
    )


def reentrancy_amount_dependency_traverse(g: GraphTraversalSource):
    return (
        g.V().hasLabel('contractCall').as_('attacker')
            .repeat(T__.out('call')).emit().as_('victim')
            .where('attacker', P.neq('victim')).by('address')
            .repeat(T__.out('call')).emit().as_('re_attacker')
            .where('attacker', P.eq('re_attacker')).by('address')
            .repeat(T__.out('call')).emit().as_('re_victim')
            .where('victim', P.eq('re_victim')).by('address')
            .local(
                T__
                .emit().repeat(T__.out('call'))
                .out('transfer').as_('victim_flow')
                .out('dataflow:read').dedup()
                .emit().repeat(T__.in_('dataflow:dependency')).dedup()
                .has('sourceType', 'Storage')
                .repeat(T__.out('dataflow:transition')).emit().as_('state_change')
                .in_('dataflow:write').as_('state_change_dcfg').dedup()
                .where(
                    T__
                    .repeat(T__.in_('jump')).emit()
                    .has_label('contractCall')
                    .emit().repeat(T__.in_('call'))
                    .where(P.eq('victim')).by('callId').count().is_(P.gt(0))
                )
                .select('victim_flow').in_('dcfg_to_asset_flow').as_('victim_flow_dcfg')
                .select('attacker', 're_attacker', 'victim', 're_victim', 'state_change', 'state_change_dcfg', 'victim_flow', 'victim_flow_dcfg').by(T__.element_map()).dedup()
            )
    )


def oracle_manipulation_traverse(g: GraphTraversalSource):
    return (
        g.V().hasLabel('assetFlow')
        .where(
            T__
            .out('dataflow:read').dedup()
            .emit().repeat(T__.in_('dataflow:dependency')).until(T__.inE('dataflow:dependency').count().is_(0)).dedup()
            .has("sourceType", "Storage").in_('dataflow:write').dedup()
            .emit().repeat(T__.in_('jump')).until(T__.inE('jump').count().is_(0))
            .in_('dataflow:control').dedup()
            .emit().repeat(T__.in_('dataflow:dependency')).until(T__.inE('dataflow:dependency').count().is_(0))
            .has("sourceType", "Caller").count().is_(P.gt(0)),
	    ).elementMap()
    )



def ABAB(g: GraphTraversalSource):
    return (
        g.V().hasLabel('contractCall').as_('attacker')
            .repeat(T__.out('call')).emit().as_('victim')
            .repeat(T__.out('call')).emit().as_('re_attacker')
            .repeat(T__.out('call')).emit().as_('re_victim')
            .where('attacker', P.eq('re_attacker')).by('address')
            .where('victim', P.eq('re_victim')).by('address')
            .where('attacker', P.neq('victim')).by('address')
            .select('attacker', 'victim', 're_attacker', 're_victim').by(T__.elementMap()).dedup()
    )


def reentrancy_filter(res: dict):
    victim_flow_dcfg_id = DcfgId.from_str(res['victim_flow_dcfg']['dcfgId'])
    state_change_dcfg_id = DcfgId.from_str(res['state_change_dcfg']['dcfgId'])
    
    if victim_flow_dcfg_id < state_change_dcfg_id:
        return True
    
    return False