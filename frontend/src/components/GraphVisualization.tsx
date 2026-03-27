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
    if (!response) {
      setGraphData(null);
      return;
    }

    // Use graph_data from API response if available
    if (response.graph_data &&
        (response.graph_data.nodes.length > 0 || response.graph_data.edges.length > 0)) {
      // Convert API format to vis-network format
      const nodes: GraphNode[] = response.graph_data.nodes.map(node => ({
        id: node.id,
        label: getDisplayLabel(node),
        group: node.label,
        title: generateNodeTooltip(node),
      }));

      const edges: GraphEdge[] = response.graph_data.edges.map(edge => ({
        from: edge.source,
        to: edge.target,
        label: edge.relationship,
        title: generateEdgeTooltip(edge),
      }));

      setGraphData({ nodes, edges });
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

// Helper functions for visualization
function getDisplayLabel(node: { label: string; properties: Record<string, any> }): string {
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

  // Use node label as fallback
  return node.label;
}

function generateNodeTooltip(node: { label: string; properties: Record<string, any> }): string {
  const props = Object.entries(node.properties)
    .map(([key, value]) => `${key}: ${value}`)
    .join('\n');

  return `${node.label}\n---\n${props}`;
}

function generateEdgeTooltip(edge: { relationship: string; properties: Record<string, any> }): string {
  if (!edge.properties || Object.keys(edge.properties).length === 0) {
    return edge.relationship;
  }

  const props = Object.entries(edge.properties)
    .map(([key, value]) => `${key}: ${value}`)
    .join('\n');

  return `${edge.relationship}\n---\n${props}`;
}

export default GraphVisualization;
