import React, { useState } from 'react';
import './App.css';

interface Hypothesis {
  id: string;
  text: string;
  confidence: number;
  provenance: string;
  timestamp: string;
}

interface ConsensusResult {
  fixedPoint: number[];
  iterations: number;
  converged: boolean;
  finalDivergence: number;
  consensusTimeMs: number;
}

function App() {
  const [prompt, setPrompt] = useState('');
  const [llm, setLlm] = useState('grok');
  const [hypothesis, setHypothesis] = useState<Hypothesis | null>(null);
  const [consensus, setConsensus] = useState<ConsensusResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [eqlQuery, setEqlQuery] = useState('');
  const [queryResults, setQueryResults] = useState<any[]>([]);

  const generateHypothesis = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, llm })
      });
      const data = await response.json();
      setHypothesis({
        id: data.hypothesis_id,
        text: data.hypothesis,
        confidence: data.confidence,
        provenance: data.provenance,
        timestamp: data.timestamp
      });
    } catch (error) {
      console.error('Error generating hypothesis:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const runConsensus = async () => {
    if (!hypothesis) return;
    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/consensus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hypothesis_id: hypothesis.id, rounds: 100 })
      });
      const data = await response.json();
      setConsensus(data.consensus);
    } catch (error) {
      console.error('Error running consensus:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const executeEQL = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ eql: eqlQuery })
      });
      const data = await response.json();
      setQueryResults(data.results || []);
    } catch (error) {
      console.error('Error executing EQL:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Gravit Open Network</h1>
        <p>Verifiable Reasoning for Autonomous Agents</p>
      </header>

      <main className="app-main">
        <section className="card">
          <h2>1. Generate Hypothesis</h2>
          <div className="form-group">
            <label>Prompt:</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Ask a question..."
              rows={3}
            />
          </div>
          <div className="form-group">
            <label>LLM:</label>
            <select value={llm} onChange={(e) => setLlm(e.target.value)}>
              <option value="grok">Grok (xAI)</option>
              <option value="gpt">GPT-4o (OpenAI)</option>
              <option value="claude">Claude (Anthropic)</option>
            </select>
          </div>
          <button onClick={generateHypothesis} disabled={isLoading}>
            {isLoading ? 'Generating...' : 'Generate'}
          </button>

          {hypothesis && (
            <div className="result">
              <h3>Generated Hypothesis</h3>
              <p><strong>ID:</strong> {hypothesis.id}</p>
              <p><strong>Text:</strong> {hypothesis.text}</p>
              <p><strong>Confidence:</strong> {(hypothesis.confidence * 100).toFixed(1)}%</p>
              <p><strong>Provenance:</strong> {hypothesis.provenance}</p>
              <button onClick={runConsensus} disabled={isLoading}>
                Run Consensus →
              </button>
            </div>
          )}
        </section>

        {consensus && (
          <section className="card">
            <h2>2. Consensus Result (GQRVP)</h2>
            <div className="result">
              <p><strong>Converged:</strong> {consensus.converged ? '✅ Yes' : '❌ No'}</p>
              <p><strong>Iterations:</strong> {consensus.iterations}</p>
              <p><strong>Final KL-Divergence:</strong> {consensus.finalDivergence.toExponential(3)}</p>
              <p><strong>Time:</strong> {consensus.consensusTimeMs.toFixed(2)} ms</p>
              <p><strong>Fixed Point Distribution:</strong></p>
              <div className="distribution">
                {consensus.fixedPoint.map((prob, i) => (
                  <div key={i} className="bar" style={{ width: `${prob * 100}%` }}>
                    Hypothesis {String.fromCharCode(65 + i)}: {(prob * 100).toFixed(1)}%
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        <section className="card">
          <h2>3. Query History (EQL)</h2>
          <div className="form-group">
            <label>EQL Query:</label>
            <input
              type="text"
              value={eqlQuery}
              onChange={(e) => setEqlQuery(e.target.value)}
              placeholder='FIND traces WHERE agent = "grok" AND consensus > 0.7'
            />
          </div>
          <button onClick={executeEQL} disabled={isLoading}>
            Execute Query
          </button>

          {queryResults.length > 0 && (
            <div className="result">
              <h3>Results ({queryResults.length})</h3>
              <pre className="query-results">
                {JSON.stringify(queryResults, null, 2)}
              </pre>
            </div>
          )}
        </section>
      </main>

      <footer className="app-footer">
        <p>Gravit Open Network — Building the standard for computable trust</p>
      </footer>
    </div>
  );
}

export default App;
