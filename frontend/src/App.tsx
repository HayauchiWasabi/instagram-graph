import { useEffect, useRef, useState, useMemo } from 'react';
// @ts-ignore
import cytoscape from 'cytoscape';
// @ts-ignore - Importing JSON directly
import graphData from './graph_data.json';
import './App.css';

interface GraphNode {
  id: string;
  label: string;
  group: string;
  processed?: boolean;
}

interface GraphEdge {
  from: string;
  to: string;
}

function App() {
  const cyRef = useRef<cytoscape.Core | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [stats, setStats] = useState({ nodes: 0, edges: 0 });

  const elements = useMemo(() => {
    const nodes = graphData.nodes.map((n: GraphNode) => ({
      data: {
        id: n.id,
        label: n.label,
        type: n.group,
        processed: n.processed
      }
    }));

    const edges = graphData.edges.map((e: GraphEdge) => ({
      data: {
        id: `${e.from}-${e.to}`,
        source: e.from,
        target: e.to
      }
    }));

    return [...nodes, ...edges];
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#4a4a4a',
            'label': 'data(label)',
            'color': '#fff',
            'font-size': '10px',
            'text-valign': 'center',
            'text-halign': 'center',
            'width': '30px',
            'height': '30px',
            'border-width': 2,
            'border-color': 'rgba(255, 255, 255, 0.1)',
            'transition-property': 'background-color, border-color, width, height',
            'transition-duration': 0.3
          }
        },
        {
          selector: 'node[type="main"]',
          style: {
            'background-color': '#ff0050',
            'width': '50px',
            'height': '50px',
            'font-size': '12px',
            'font-weight': 'bold',
            'border-color': '#fff'
          }
        },
        {
          selector: 'node[processed]',
          style: {
            'border-color': '#00f2fe',
            'border-width': 3
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 1,
            'line-color': 'rgba(255, 255, 255, 0.1)',
            'curve-style': 'haystack', // High performance for many edges
            'opacity': 0.3
          }
        },
        {
          selector: '.highlighted',
          style: {
            'background-color': '#00f2fe',
            'line-color': '#00f2fe',
            'width': 4,
            'opacity': 1,
            'z-index': 999
          }
        },
        {
          selector: '.dimmed',
          style: {
            'opacity': 0.1
          }
        }
      ],
      layout: {
        name: 'cose',
        randomize: true,
        nodeRepulsion: 100000, // 大幅に反発を強く
        idealEdgeLength: 200,   // エッジを長くして広げる
        componentSpacing: 100,       // コンポーネント間の距離
        nodeOverlap: 20,             // 重なりを避ける
        animate: true,
        refresh: 20,
        animationDuration: 1500,
        ready: () => setLoading(false),
        stop: () => setLoading(false)
      }
    });

    cy.on('tap', 'node', (evt: any) => {
      const node = evt.target;
      const neighborhood = node.neighborhood().add(node);

      cy.elements().addClass('dimmed').removeClass('highlighted');
      neighborhood.removeClass('dimmed').addClass('highlighted');
    });

    cy.on('tap', (evt: any) => {
      if (evt.target === cy) {
        cy.elements().removeClass('dimmed').removeClass('highlighted');
      }
    });

    cyRef.current = cy;
    setStats({ nodes: graphData.nodes.length, edges: graphData.edges.length });

    return () => {
      cy.destroy();
    };
  }, [elements]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!cyRef.current || !searchTerm) return;

    const node = cyRef.current.$(`node[id *= "${searchTerm}"]`);
    if (node.length > 0) {
      cyRef.current.animate({
        center: { eles: node },
        zoom: 2,
        duration: 500
      });
      node.trigger('tap');
    }
  };

  return (
    <div className="app-container">
      <div className="sidebar">
        <h1>InstaGraph</h1>

        <div className="stat-card">
          <div className="stat-label">Total Nodes</div>
          <div className="stat-value">{stats.nodes}</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Connections</div>
          <div className="stat-value">{stats.edges}</div>
        </div>

        <form className="search-container" onSubmit={handleSearch}>
          <div className="stat-label" style={{ marginBottom: '8px' }}>Search Friend</div>
          <input
            type="text"
            placeholder="Username..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </form>

        <div style={{ marginTop: 'auto', fontSize: '12px', color: 'rgba(255,255,255,0.3)' }}>
          Tip: Click a node to highlight its connections. Click on background to reset.
        </div>
      </div>

      <div className="graph-container">
        {loading && (
          <div className="loading-overlay">
            <div className="spinner"></div>
            <div>Mapping Relationships...</div>
          </div>
        )}
        <div id="cy" ref={containerRef}></div>
      </div>
    </div>
  );
}

export default App;
