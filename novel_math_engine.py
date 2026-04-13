"""
HyperMorph Algebra Engine (HMAE)
================================
A speculative mathematics sandbox that defines a new algebra over
"phase-annotated tensors" and "curvature-aware operators".

This file is intentionally rich and expressive: it combines symbolic
composition, lazy evaluation, custom invariants, and numerical probing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Mapping, MutableMapping, Tuple
import cmath
import math
import random


Scalar = complex
Coord = Tuple[int, ...]


@dataclass(frozen=True)
class PhaseTensor:
    """
    Core object in the new math system.

    A PhaseTensor stores:
    - components indexed by N-dimensional integer coordinates,
    - a global phase anchor,
    - a local curvature coefficient.

    Multiplication is non-commutative due to curvature transport.
    """

    components: Mapping[Coord, Scalar]
    phase_anchor: float = 0.0
    curvature: float = 0.0

    def rank(self) -> int:
        if not self.components:
            return 0
        return len(next(iter(self.components.keys())))

    def support(self) -> int:
        return len(self.components)

    def norm(self) -> float:
        return math.sqrt(sum((abs(v) ** 2 for v in self.components.values())))

    def rephased(self, delta: float) -> "PhaseTensor":
        rot = cmath.exp(1j * delta)
        return PhaseTensor(
            {k: v * rot for k, v in self.components.items()},
            phase_anchor=self.phase_anchor + delta,
            curvature=self.curvature,
        )

    def sparse_map(self, fn: Callable[[Coord, Scalar], Scalar]) -> "PhaseTensor":
        return PhaseTensor(
            {k: fn(k, v) for k, v in self.components.items()},
            phase_anchor=self.phase_anchor,
            curvature=self.curvature,
        )


@dataclass(frozen=True)
class HyperOperator:
    """
    A curvature-aware transformation over PhaseTensor.

    The kernel maps input coordinates to output coordinates with weights.
    """

    kernel: Mapping[Tuple[Coord, Coord], Scalar]
    torsion: float = 0.0
    gain: float = 1.0

    def apply(self, tensor: PhaseTensor) -> PhaseTensor:
        out: MutableMapping[Coord, Scalar] = {}
        rank = tensor.rank()
        if rank == 0:
            return tensor

        for (src, dst), w in self.kernel.items():
            if src in tensor.components:
                transported = tensor.components[src] * w
                phase_twist = cmath.exp(1j * self.torsion * (sum(dst) - sum(src)))
                out[dst] = out.get(dst, 0) + self.gain * transported * phase_twist

        curvature_shift = tensor.curvature + self.torsion * 0.5
        return PhaseTensor(
            out,
            phase_anchor=tensor.phase_anchor + self.torsion,
            curvature=curvature_shift,
        )


@dataclass
class MorphicProgram:
    """
    Lazy compositional program in the novel system.

    It supports:
    - staged operator chains,
    - fixed-point resonance search,
    - entropy-regularized evaluation.
    """

    operators: List[HyperOperator] = field(default_factory=list)
    entropy_lambda: float = 0.02

    def push(self, op: HyperOperator) -> "MorphicProgram":
        self.operators.append(op)
        return self

    def run(self, x: PhaseTensor, steps: int | None = None) -> PhaseTensor:
        y = x
        ops = self.operators if steps is None else self.operators[:steps]
        for op in ops:
            y = op.apply(y)
            y = self._entropy_regularize(y)
        return y

    def _entropy_regularize(self, x: PhaseTensor) -> PhaseTensor:
        if not x.components:
            return x

        mag_sum = sum(abs(v) for v in x.components.values()) + 1e-12

        def shrink(_: Coord, v: Scalar) -> Scalar:
            p = abs(v) / mag_sum
            local_entropy = -p * math.log(p + 1e-12)
            penalty = math.exp(-self.entropy_lambda * local_entropy)
            return v * penalty

        return x.sparse_map(shrink)

    def resonance_index(
        self,
        seed: PhaseTensor,
        trials: int = 32,
        depth: int = 4,
        jitter: float = 0.03,
    ) -> float:
        """
        Empirical stability score for this program.

        We perturb the seed phase, run partial chains, and measure
        averaged normalized overlap.
        """
        if not seed.components:
            return 0.0

        def overlap(a: PhaseTensor, b: PhaseTensor) -> float:
            keys = set(a.components) | set(b.components)
            num = sum((a.components.get(k, 0).conjugate() * b.components.get(k, 0) for k in keys))
            den = (a.norm() * b.norm()) + 1e-12
            return abs(num / den)

        base = self.run(seed, steps=depth)
        scores = []
        for _ in range(trials):
            d = random.uniform(-jitter, jitter)
            perturbed = seed.rephased(d)
            out = self.run(perturbed, steps=depth)
            scores.append(overlap(base, out))

        return float(sum(scores) / len(scores))


# --- Novel primitives ------------------------------------------------------


def weave_operator(rank: int, span: int, torsion: float, gain: float = 1.0) -> HyperOperator:
    """
    Generate a deterministic weave kernel.

    New rule idea:
    Each coordinate shifts by +/- 1 based on parity, creating
    braided transport lanes in coordinate-space.
    """
    kernel: Dict[Tuple[Coord, Coord], Scalar] = {}

    def dst_of(src: Coord) -> Coord:
        out = []
        for i, c in enumerate(src):
            direction = 1 if (i + c) % 2 == 0 else -1
            out.append(c + direction)
        return tuple(out)

    coords = _bounded_coords(rank, span)
    for src in coords:
        dst = dst_of(src)
        weight = cmath.exp(1j * 0.1 * sum(src)) / (1 + abs(sum(dst)))
        kernel[(src, dst)] = weight

    return HyperOperator(kernel=kernel, torsion=torsion, gain=gain)


def seed_tensor(rank: int, span: int, phase_anchor: float = 0.0, curvature: float = 0.1) -> PhaseTensor:
    comps: Dict[Coord, Scalar] = {}
    for c in _bounded_coords(rank, span):
        radius = math.sqrt(sum(x * x for x in c))
        amp = math.exp(-0.35 * radius)
        phase = phase_anchor + 0.2 * sum(c)
        comps[c] = amp * cmath.exp(1j * phase)
    return PhaseTensor(comps, phase_anchor=phase_anchor, curvature=curvature)


def derive_axiom_signature(program: MorphicProgram, seed: PhaseTensor) -> Dict[str, float]:
    """
    Compute a compact fingerprint for this new algebraic system.

    Axioms (heuristic):
    - coherence: mean resonance stability
    - drift: expected phase displacement
    - curvature_gain: average curvature amplification
    """
    y = program.run(seed)
    coherence = program.resonance_index(seed, trials=24, depth=min(5, len(program.operators) or 1))
    drift = abs(y.phase_anchor - seed.phase_anchor)
    curvature_gain = (y.curvature + 1e-9) / (seed.curvature + 1e-9)

    return {
        "coherence": float(coherence),
        "drift": float(drift),
        "curvature_gain": float(curvature_gain),
        "support_growth": float((y.support() + 1e-9) / (seed.support() + 1e-9)),
    }


def _bounded_coords(rank: int, span: int) -> Iterable[Coord]:
    if rank <= 0:
        return [tuple()]

    ranges = [range(-span, span + 1) for _ in range(rank)]

    def rec(i: int, cur: List[int]):
        if i == rank:
            yield tuple(cur)
            return
        for v in ranges[i]:
            cur.append(v)
            yield from rec(i + 1, cur)
            cur.pop()

    return list(rec(0, []))


def demo() -> None:
    random.seed(7)

    rank, span = 3, 1
    seed = seed_tensor(rank=rank, span=span, phase_anchor=0.15, curvature=0.22)

    prog = MorphicProgram(entropy_lambda=0.04)
    prog.push(weave_operator(rank, span, torsion=0.21, gain=1.10))
    prog.push(weave_operator(rank, span, torsion=-0.13, gain=0.95))
    prog.push(weave_operator(rank, span, torsion=0.09, gain=1.05))

    signature = derive_axiom_signature(prog, seed)
    print("HyperMorph Axiom Signature")
    for k, v in signature.items():
        print(f"- {k}: {v:.6f}")


if __name__ == "__main__":
    demo()
