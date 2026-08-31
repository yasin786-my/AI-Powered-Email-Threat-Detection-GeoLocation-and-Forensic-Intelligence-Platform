"""
Module 4: Identity Correlation & Campaign Attribution
Uses NetworkX to link emails by shared infrastructure (IP, domain, registrar).
"""

import networkx as nx
import json

# Global in-memory graph (persists across requests within one server session)
G = nx.Graph()


def add_email_to_graph(email_id, header_data, geo_data):
    """
    Add an analyzed email to the campaign correlation graph.
    Creates nodes for the email, its IP, domain, and registrar,
    then edges between them.
    """
    G.add_node(email_id, type="email", label=header_data.get("subject", email_id)[:40])

    ip = geo_data.get("earliest_hop_ip")
    domain = header_data.get("from_domain")
    registrar = geo_data.get("whois_registrar")

    if ip:
        G.add_node(ip, type="ip")
        G.add_edge(email_id, ip, relation="sent_from")

    if domain:
        G.add_node(domain, type="domain")
        G.add_edge(email_id, domain, relation="from_domain")

    if registrar:
        registrar_clean = registrar.strip()[:50]
        G.add_node(registrar_clean, type="registrar")
        G.add_edge(email_id, registrar_clean, relation="registered_by")
        if domain:
            G.add_edge(domain, registrar_clean, relation="registered_at")

    return get_graph_data()


def find_campaign(email_id):
    """
    Find all emails connected to the given email through shared infrastructure.
    Returns linked emails, shared infrastructure, and confidence score.
    """
    if email_id not in G:
        return {"linked_emails": [], "shared_infra": [], "confidence": 0, "campaign_size": 0}

    connected = nx.node_connected_component(G, email_id)

    linked_emails = [
        n for n in connected
        if G.nodes[n].get("type") == "email" and n != email_id
    ]

    shared_infra = [
        {"node": n, "type": G.nodes[n].get("type")}
        for n in connected
        if G.nodes[n].get("type") != "email"
    ]

    # Confidence: more shared infrastructure = higher confidence
    if linked_emails:
        infra_count = len(shared_infra)
        confidence = min(len(linked_emails) * 25 + infra_count * 10 + 15, 100)
    else:
        confidence = 0

    return {
        "linked_emails": linked_emails,
        "shared_infra": shared_infra,
        "confidence": confidence,
        "campaign_size": len(linked_emails) + 1,
    }


def get_graph_data():
    """
    Export the full graph as JSON suitable for frontend visualization.
    Returns nodes and edges in a format compatible with react-force-graph.
    """
    nodes = []
    for node_id, attrs in G.nodes(data=True):
        node_type = attrs.get("type", "unknown")
        nodes.append({
            "id": node_id,
            "type": node_type,
            "label": attrs.get("label", node_id),
            "group": node_type,
        })

    edges = []
    for source, target, attrs in G.edges(data=True):
        edges.append({
            "source": source,
            "target": target,
            "relation": attrs.get("relation", "linked"),
        })

    return {"nodes": nodes, "edges": edges}


def clear_graph():
    """Reset the campaign graph."""
    G.clear()
    return {"nodes": [], "edges": []}
