import React, { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network';
import { DataSet } from 'vis-network/standalone';
import { QueryResponse } from '../services/api';
import './GraphVisualization.css';

interface GraphVisualizationProps {
  response: QueryResponse | null;
}

interface GraphNode {
  id: string;
  label: string;
  group?: string;
  title?: string;
}

interface GraphEdge {
  from: string;
  to: string;
  label?: string;
  title?: string;
}

const GraphVisualization: React.FC<GraphVisualizationProps> = ({ response }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const [isVisible, setIsVisible] = useState(true);
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] } | null>(null);

  useEffect(() => {
    if (!response || !response.results || response.results.length === 0) {
      setGraphData(null);
      return;
    }

    // Extract graph data from results
    const extractedData = extractGraphData(response.results);

    // Only set graph data if there are actual nodes or edges
    if (extractedData.nodes.length > 0 || extractedData.edges.length > 0) {
      setGraphData(extractedData);
    } else {
      setGraphData(null);
    }
  }, [response]);

  useEffect(() => {
    if (!containerRef.current || !graphData || !isVisible) {
      return;
    }

    // Create vis-network graph
    const nodes = new DataSet(graphData.nodes);
    const edges = new DataSet(graphData.edges);

    const data = { nodes, edges };

    const options = {
      nodes: {
        shape: 'dot',
        size: 20,
        font: {
          size: 14,
          color: '#ffffff',
        },
        borderWidth: 2,
        borderWidthSelected: 4,
      },
      edges: {
        width: 2,
        color: { color: '#848484', highlight: '#646cff' },
        arrows: {
          to: { enabled: true, scaleFactor: 0.5 },
        },
        font: {
          size: 12,
          color: '#ffffff',
          align: 'middle',
        },
        smooth: {
          type: 'continuous',
        },
      },
      physics: {
        stabilization: {
          iterations: 200,
        },
        barnesHut: {
          gravitationalConstant: -2000,
          springConstant: 0.001,
          springLength: 200,
        },
      },
      interaction: {
        hover: true,
        tooltipDelay: 100,
        zoomView: true,
        dragView: true,
      },
      groups: {
        Person: { color: { background: '#FF6B6B', border: '#C92A2A' } },
        Crime: { color: { background: '#845EC2', border: '#5F3B8C' } },
        Location: { color: { background: '#00C9A7', border: '#008F75' } },
        Vehicle: { color: { background: '#FFC75F', border: '#C98C2E' } },
        Object: { color: { background: '#F9F871', border: '#C7C74E' } },
        Officer: { color: { background: '#4D96FF', border: '#3270CC' } },
        Phone: { color: { background: '#B39CD0', border: '#8A6FA6' } },
        Email: { color: { background: '#FF9671', border: '#CC6945' } },
        AREA: { color: { background: '#00D2FF', border: '#00A0CC' } },
        PostCode: { color: { background: '#A8DADC', border: '#7FADB0' } },
        default: { color: { background: '#97C2FC', border: '#2B7CE9' } },
      },
    };

    networkRef.current = new Network(containerRef.current, data, options);

    // Cleanup
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [graphData, isVisible]);

  if (!response || !graphData || graphData.nodes.length === 0) {
    return null;
  }

  return (
    <div className="graph-visualization">
      <div className="graph-header">
        <h2>Graph Visualization</h2>
        <div className="graph-controls">
          <span className="node-count">
            {graphData.nodes.length} nodes, {graphData.edges.length} edges
          </span>
          <button
            className="toggle-graph-button"
            onClick={() => setIsVisible(!isVisible)}
          >
            {isVisible ? 'Hide Graph' : 'Show Graph'}
          </button>
        </div>
      </div>

      {isVisible && (
        <div className="graph-container" ref={containerRef}></div>
      )}
    </div>
  );
};

// Helper function to extract graph data from query results
function extractGraphData(results: Array<Record<string, any>>): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodes = new Map<string, GraphNode>();
  const edges: GraphEdge[] = [];
  let edgeId = 0;

  results.forEach((row) => {
    Object.entries(row).forEach(([key, value]) => {
      // Check if value is a node (Neo4j node object)
      if (isNode(value)) {
        const nodeId = getNodeId(value);
        if (!nodes.has(nodeId)) {
          nodes.set(nodeId, {
            id: nodeId,
            label: getNodeLabel(value),
            group: getNodeGroup(value),
            title: getNodeTooltip(value),
          });
        }
      }
      // Check if value is a relationship (Neo4j relationship object)
      else if (isRelationship(value)) {
        edges.push({
          from: String(value.start),
          to: String(value.end),
          label: value.type || '',
          title: getRelationshipTooltip(value),
        });
      }
      // Check if value is a path (Neo4j path object)
      else if (isPath(value)) {
        // Extract nodes and relationships from path
        if (value.segments) {
          value.segments.forEach((segment: any) => {
            if (segment.start) {
              const startId = getNodeId(segment.start);
              if (!nodes.has(startId)) {
                nodes.set(startId, {
                  id: startId,
                  label: getNodeLabel(segment.start),
                  group: getNodeGroup(segment.start),
                  title: getNodeTooltip(segment.start),
                });
              }
            }
            if (segment.end) {
              const endId = getNodeId(segment.end);
              if (!nodes.has(endId)) {
                nodes.set(endId, {
                  id: endId,
                  label: getNodeLabel(segment.end),
                  group: getNodeGroup(segment.end),
                  title: getNodeTooltip(segment.end),
                });
              }
            }
            if (segment.relationship) {
              edges.push({
                from: getNodeId(segment.start),
                to: getNodeId(segment.end),
                label: segment.relationship.type || '',
                title: getRelationshipTooltip(segment.relationship),
              });
            }
          });
        }
      }
    });
  });

  return {
    nodes: Array.from(nodes.values()),
    edges,
  };
}

// Type guards and helper functions
function isNode(value: any): boolean {
  return value && typeof value === 'object' && 'identity' in value && 'labels' in value;
}

function isRelationship(value: any): boolean {
  return value && typeof value === 'object' && 'type' in value && 'start' in value && 'end' in value;
}

function isPath(value: any): boolean {
  return value && typeof value === 'object' && 'segments' in value;
}

function getNodeId(node: any): string {
  return node.identity?.toString() || node.id?.toString() || String(Math.random());
}

function getNodeGroup(node: any): string {
  if (node.labels && node.labels.length > 0) {
    return node.labels[0];
  }
  return 'default';
}

function getNodeLabel(node: any): string {
  if (!node.properties) return 'Node';

  // Try common name properties
  const nameProps = ['name', 'surname', 'type', 'description', 'address', 'make', 'model', 'phoneNo', 'email_address', 'code', 'areaCode'];
  for (const prop of nameProps) {
    if (node.properties[prop]) {
      return String(node.properties[prop]);
    }
  }

  // Try to combine name and surname
  if (node.properties.name || node.properties.surname) {
    const parts = [node.properties.name, node.properties.surname].filter(Boolean);
    return parts.join(' ');
  }

  // Use label if available
  if (node.labels && node.labels.length > 0) {
    return node.labels[0];
  }

  return 'Node';
}

function getNodeTooltip(node: any): string {
  if (!node.properties) return '';

  const props = Object.entries(node.properties)
    .map(([key, value]) => `${key}: ${value}`)
    .join('\n');

  const label = node.labels ? node.labels.join(', ') : '';
  return label ? `${label}\n---\n${props}` : props;
}

function getRelationshipTooltip(rel: any): string {
  if (!rel.properties || Object.keys(rel.properties).length === 0) {
    return rel.type || '';
  }

  const props = Object.entries(rel.properties)
    .map(([key, value]) => `${key}: ${value}`)
    .join('\n');

  return `${rel.type || 'Relationship'}\n---\n${props}`;
}

export default GraphVisualization;
