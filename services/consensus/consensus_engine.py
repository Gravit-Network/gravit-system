"""
GQRVP Consensus Engine

This service implements the Gravit Quantum Resilient Verification Protocol
using the mathematical core from gravit-truth-consensus.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Import from mathematical core
try:
    from gravit_truth_consensus.consensus import run_consensus, kl_divergence
    from gravit_truth_consensus.byzantine import ByzantineDetector
    GTC_AVAILABLE = True
except ImportError:
    GTC_AVAILABLE = False
    print("Warning: gravit-truth-consensus not installed. Using fallback.")


@dataclass
class ConsensusResult:
    """Result of a consensus round."""
    fixed_point: np.ndarray
    iterations: int
    converged: bool
    final_divergence: float
    byzantine_fraction: float
    contamination_bound: Optional[float] = None


class GQRVPEngine:
    """
    Gravit Quantum Resilient Verification Protocol Engine.

    Implements the consensus algorithm from the formal specification.
    """

    def __init__(self, n_agents: int = 100, n_hypotheses: int = 3):
        self.n_agents = n_agents
        self.n_hypotheses = n_hypotheses
        self.graph = self._create_graph()
        self.byzantine_detector = ByzantineDetector(n_agents) if GTC_AVAILABLE else None

    def _create_graph(self) -> np.ndarray:
        """Create Erdos-Renyi communication graph."""
        p = 0.3  # connection probability
        graph = np.random.rand(self.n_agents, self.n_agents) < p
        graph = (graph + graph.T) / 2
        np.fill_diagonal(graph, 1)
        # Row-stochastic normalization
        graph = graph / graph.sum(axis=1, keepdims=True)
        return graph

    def run_consensus(
        self,
        hypotheses: List[Dict[str, Any]],
        initial_beliefs: Optional[np.ndarray] = None,
        max_iterations: int = 1000,
        tolerance: float = 1e-6
    ) -> ConsensusResult:
        """
        Run consensus on a set of hypotheses.

        Args:
            hypotheses: List of hypothesis dictionaries
            initial_beliefs: Initial probability distributions (n_agents x n_hypotheses)
            max_iterations: Maximum number of iterations
            tolerance: Convergence tolerance

        Returns:
            ConsensusResult with fixed point and metadata
        """
        if GTC_AVAILABLE:
            return self._run_with_gtc(hypotheses, max_iterations, tolerance)
        else:
            return self._run_fallback(hypotheses, max_iterations, tolerance)

    def _run_with_gtc(
        self,
        hypotheses: List[Dict],
        max_iterations: int,
        tolerance: float
    ) -> ConsensusResult:
        """Use the mathematical core implementation."""
        # Convert hypotheses to signals
        signals = self._hypotheses_to_signals(hypotheses)

        # Run consensus from gravit-truth-consensus
        result = run_consensus(
            graph=self.graph,
            signals=signals,
            max_iter=max_iterations,
            tol=tolerance
        )

        return ConsensusResult(
            fixed_point=result['fixed_point'],
            iterations=result['iterations'],
            converged=result['converged'],
            final_divergence=result['final_kl_divergence'],
            byzantine_fraction=result.get('byzantine_fraction', 0.0),
            contamination_bound=result.get('contamination_bound')
        )

    def _run_fallback(
        self,
        hypotheses: List[Dict],
        max_iterations: int,
        tolerance: float
    ) -> ConsensusResult:
        """Fallback implementation if GTC not available."""
        # Initialize beliefs uniformly
        beliefs = np.ones((self.n_agents, self.n_hypotheses)) / self.n_hypotheses

        for i in range(max_iterations):
            # Bayesian update step
            signals = self._hypotheses_to_signals(hypotheses)
            beliefs = beliefs * np.exp(signals)
            beliefs = beliefs / beliefs.sum(axis=1, keepdims=True)

            # Gossip averaging step
            beliefs = (1 - 0.3) * beliefs + 0.3 * (self.graph @ beliefs)

            # Check convergence
            if i > 0:
                divergence = np.mean(kl_divergence(beliefs, prev_beliefs))
                if divergence < tolerance:
                    return ConsensusResult(
                        fixed_point=beliefs[0],
                        iterations=i,
                        converged=True,
                        final_divergence=divergence,
                        byzantine_fraction=0.0
                    )
            prev_beliefs = beliefs.copy()

        return ConsensusResult(
            fixed_point=beliefs[0],
            iterations=max_iterations,
            converged=False,
            final_divergence=divergence,
            byzantine_fraction=0.0
        )

    def _hypotheses_to_signals(self, hypotheses: List[Dict]) -> np.ndarray:
        """Convert hypothesis dictionaries to signal matrix."""
        signals = np.zeros((self.n_agents, self.n_hypotheses))
        for i, hyp in enumerate(hypotheses[:self.n_hypotheses]):
            confidence = hyp.get('confidence', 0.5)
            signals[:, i] = np.log(confidence / (1 - confidence))
        return signals
