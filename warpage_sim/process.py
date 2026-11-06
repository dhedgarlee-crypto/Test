"""Sequential process simulation of a panel (layer birth, cure shrinkage, thermal
excursions, grinding, carrier removal, flipping) with incremental classical laminate theory.

Every layer is born stress-free on the deformed panel at its birth temperature (e.g. the
cure / mold temperature) and from then on follows the panel. z is absolute (z = 0 at the
bottom of the first carrier) and never changes, so the curvature kappa is the true
cumulative curvature of the panel since the flat starting carrier.

Stress in each layer is linear through its thickness (incremental elastic), stored at the
layer bottom/top; grinding and removal release the cut material's force/moment resultants.
Limitation: temperature-dependent elastic (no viscoelastic relaxation yet).
"""
from dataclasses import dataclass, field
import numpy as np

GAUSS2 = (np.array([-1, 1]) / np.sqrt(3), np.array([1.0, 1.0]))


@dataclass
class PLayer:
    id: str
    group: str
    mat: object            # Material / CompositeMaterial (zone-specific)
    zb: float
    zt: float
    sb: np.ndarray = field(default_factory=lambda: np.zeros(3))
    st: np.ndarray = field(default_factory=lambda: np.zeros(3))

    @property
    def t(self):
        return self.zt - self.zb

    def sigma(self, z):
        s = (z - self.zb) / max(self.t, 1e-15)
        return self.sb + (self.st - self.sb) * s


class PanelState:
    """Laminate state of one in-plane zone (e.g. unit array or edge frame)."""

    def __init__(self, T0):
        self.layers: list[PLayer] = []
        self.T = T0
        self.eps0 = np.zeros(3)
        self.kappa = np.zeros(3)

    # ---------------- laminate matrices ----------------
    def abd(self, T):
        A = np.zeros((3, 3)); B = np.zeros((3, 3)); D = np.zeros((3, 3))
        for L in self.layers:
            Q = L.mat.Q(T)
            A += Q * (L.zt - L.zb)
            B += Q * (L.zt ** 2 - L.zb ** 2) / 2
            D += Q * (L.zt ** 3 - L.zb ** 3) / 3
        return A, B, D

    def _deform(self, T, N, M, eig=None):
        """Apply load resultants (N, M); eig: {layer: eigenstrain vector} for stress update."""
        A, B, D = self.abd(T)
        d = np.linalg.solve(np.block([[A, B], [B, D]]), np.concatenate([N, M]))
        de, dk = d[:3], d[3:]
        self.eps0 += de; self.kappa += dk
        for L in self.layers:
            Q = L.mat.Q(T)
            e = eig.get(L.id, 0.0) if eig else 0.0
            L.sb = L.sb + Q @ (de + L.zb * dk - e)
            L.st = L.st + Q @ (de + L.zt * dk - e)

    def _eigen_load(self, T, eig):
        N = np.zeros(3); M = np.zeros(3)
        for L in self.layers:
            if L.id in eig:
                Qe = L.mat.Q(T) @ eig[L.id]
                N += Qe * L.t
                M += Qe * (L.zt ** 2 - L.zb ** 2) / 2
        return N, M

    # ---------------- process operations ----------------
    @property
    def top(self):
        return self.layers[-1].zt if self.layers else 0.0

    def add(self, lid, group, mat, t):
        z0 = self.top
        self.layers.append(PLayer(lid, group, mat, z0, z0 + t))

    def cure_shrink(self, lids):
        eig = {}
        for L in self.layers:
            if L.id in lids:
                e = L.mat.shrinkage_strain(self.T)   # signed: negative = shrink
                if e != 0:
                    eig[L.id] = np.array([e, e, 0.0])
        if eig:
            N, M = self._eigen_load(self.T, eig)
            self._deform(self.T, N, M, eig)

    def temp_to(self, T1, dT_max=2.0):
        n = max(1, int(np.ceil(abs(T1 - self.T) / dT_max)))
        Ts = np.linspace(self.T, T1, n + 1)
        for i in range(n):
            T = 0.5 * (Ts[i] + Ts[i + 1]); dT = Ts[i + 1] - Ts[i]
            eig = {L.id: L.mat.alpha(T) * dT for L in self.layers}
            N, M = self._eigen_load(T, eig)
            self._deform(T, N, M, eig)
        self.T = T1

    @staticmethod
    def _resultants(L, z0, z1):
        """Force/moment resultants of layer L's stress over [z0, z1] (exact, 2-pt Gauss)."""
        g, w = GAUSS2
        zm, h = 0.5 * (z0 + z1), 0.5 * (z1 - z0)
        N = np.zeros(3); M = np.zeros(3)
        for gi, wi in zip(g, w):
            z = zm + h * gi
            s = L.sigma(z)
            N += wi * h * s; M += wi * h * s * z
        return N, M

    def grind(self, lid, t_new):
        L = self.layers[-1]
        if L.id != lid:
            raise ValueError(f"grind: {lid} is not the top layer (top is {L.id})")
        zc = L.zb + t_new
        N, M = self._resultants(L, zc, L.zt)
        sc = L.sigma(zc)
        L.zt, L.st = zc, sc
        self._deform(self.T, N, M)

    def remove(self, lids):
        lids = set(lids)
        idx = [i for i, L in enumerate(self.layers) if L.id in lids or L.group in lids]
        if not idx:
            raise ValueError(f"remove: nothing matches {lids}")
        n = len(self.layers)
        if not (idx == list(range(len(idx))) or idx == list(range(n - len(idx), n))):
            raise ValueError("remove: only a contiguous block at the top or bottom can be removed")
        N = np.zeros(3); M = np.zeros(3)
        for i in idx:
            Ni, Mi = self._resultants(self.layers[i], self.layers[i].zb, self.layers[i].zt)
            N += Ni; M += Mi
        self.layers = [L for i, L in enumerate(self.layers) if i not in idx]
        self._deform(self.T, N, M)

    # ---------------- outputs ----------------
    def residual(self):
        N = np.zeros(3); M = np.zeros(3)
        for L in self.layers:
            Ni, Mi = self._resultants(L, L.zb, L.zt); N += Ni; M += Mi
        return N, M

    def thickness(self):
        return self.layers[-1].zt - self.layers[0].zb

    def Dstar(self):
        A, B, D = self.abd(self.T)
        return D - B @ np.linalg.solve(A, B)

    def areal_mass(self):
        return sum(L.mat.rho * L.t for L in self.layers)

    def flatten_stresses(self):
        """Layer stresses (bottom/top, MPa) after the chuck forces the panel flat."""
        A, B, D = self.abd(self.T)
        dk = -self.kappa
        de = -np.linalg.solve(A, B @ dk)
        out = []
        for L in self.layers:
            Q = L.mat.Q(self.T)
            sb = L.sb + Q @ (de + L.zb * dk); st = L.st + Q @ (de + L.zt * dk)
            out.append((L, sb / 1e6, st / 1e6))
        return out
