"""Temperature-dependent material models (SI units: Pa, 1/K, kg/m^3, degC)."""
from dataclasses import dataclass
import numpy as np


@dataclass
class Material:
    """Single-phase material; tanh transition between glassy and rubbery values around Tg."""
    name: str
    E_glassy: float          # Pa, modulus below Tg
    nu: float
    alpha_x_glassy: float    # 1/K, CTE below Tg (in-plane x)
    rho: float               # kg/m^3
    alpha_y_glassy: float | None = None   # None -> same as x (in-plane isotropic)
    E_rubbery: float | None = None        # None -> no Tg transition
    alpha_x_rubbery: float | None = None
    alpha_y_rubbery: float | None = None
    Tg: float = 1e9                       # degC
    Tg_width: float = 8.0                 # degC, width of tanh transition
    allowable_stress: float | None = None # Pa, tensile allowable for flattening check
    cure_shrinkage: float = 0.0           # linear in-plane cure shrinkage strain (positive number)

    def _blend(self, T, low, high):
        if high is None or self.Tg > 1e8:
            return low
        s = 0.5 * (1.0 + np.tanh((T - self.Tg) / self.Tg_width))  # 0 glassy -> 1 rubbery
        return low + (high - low) * s

    def E(self, T):
        return self._blend(T, self.E_glassy, self.E_rubbery)

    def alpha(self, T):
        ay_g = self.alpha_y_glassy if self.alpha_y_glassy is not None else self.alpha_x_glassy
        ax_r = self.alpha_x_rubbery
        ay_r = self.alpha_y_rubbery if self.alpha_y_rubbery is not None else ax_r
        return np.array([self._blend(T, self.alpha_x_glassy, ax_r),
                         self._blend(T, ay_g, ay_r), 0.0])

    def Q(self, T):
        E, nu = self.E(T), self.nu
        c = E / (1 - nu ** 2)
        return np.array([[c, nu * c, 0], [nu * c, c, 0], [0, 0, E / (2 * (1 + nu))]])

    def shrinkage_strain(self, T):
        return -self.cure_shrinkage

    @classmethod
    def from_dict(cls, d):
        units = {"E_glassy": 1e9, "E_rubbery": 1e9, "alpha_x_glassy": 1e-6, "alpha_y_glassy": 1e-6,
                 "alpha_x_rubbery": 1e-6, "alpha_y_rubbery": 1e-6, "allowable_stress": 1e6,
                 "cure_shrinkage": 1e-2}
        kw = {}
        for k, v in d.items():
            if k.startswith("_"):
                continue
            kw[k] = v * units[k] if (k in units and v is not None) else v
        return cls(**kw)


@dataclass
class Layer:
    material: Material
    thickness: float  # m


class TabulatedMaterial(Material):
    """Material whose E(T) and CTE(T) come from measured tables (DMA / TMA), linearly
    interpolated; outside the table range the end values are held. CTE must be the
    instantaneous (tangent) CTE, not the secant/average CTE."""

    def __init__(self, base: Material, T, E, ax, ay=None):
        self.__dict__.update(base.__dict__)
        o = np.argsort(T)
        self._T = np.asarray(T, float)[o]
        self._E = np.asarray(E, float)[o]
        self._ax = np.asarray(ax, float)[o]
        self._ay = np.asarray(ay if ay is not None else ax, float)[o]

    def E(self, T):
        return float(np.interp(T, self._T, self._E))

    def alpha(self, T):
        return np.array([np.interp(T, self._T, self._ax), np.interp(T, self._T, self._ay), 0.0])


class CompositeMaterial:
    """Homogenized in-plane properties of a layer made of a matrix plus up to N inclusions
    (Cu lines/vias, Cu posts, Si dies...). Mixing rules:
      voigt  : continuous in-plane phases (Cu lines/planes)      E = sum(phi_i E_i)
      halpin : columns / blocks in a matrix (vias, posts, dies)  Halpin-Tsai, xi = 2
      reuss  : lower bound                                       1/E = sum(phi_i / E_i)
    CTE is the stiffness-weighted (Turner) average. All properties stay temperature dependent.
    """

    def __init__(self, name, matrix, inclusions, rule="voigt"):
        self.name = name
        self.matrix = matrix
        self.inclusions = [(m, f) for m, f in inclusions if f > 0]
        self.rule = rule.lower()
        fsum = sum(f for _, f in self.inclusions)
        if fsum >= 1.0:
            raise ValueError(f"{name}: inclusion fractions sum to {fsum:.2f} >= 1")
        self.phi_m = 1.0 - fsum
        phases = [(matrix, self.phi_m)] + self.inclusions
        self.nu = sum(m.nu * f for m, f in phases)
        self.rho = sum(m.rho * f for m, f in phases)
        self.allowable_stress = None
        self.cure_shrinkage = getattr(matrix, "cure_shrinkage", 0.0)

    def _phases(self):
        return [(self.matrix, self.phi_m)] + self.inclusions

    def E(self, T):
        ph = self._phases()
        if not self.inclusions:
            return self.matrix.E(T)
        if self.rule == "voigt":
            return sum(m.E(T) * f for m, f in ph)
        if self.rule == "reuss":
            return 1.0 / sum(f / m.E(T) for m, f in ph)
        # Halpin-Tsai with the inclusions lumped (Voigt among themselves)
        phi = 1.0 - self.phi_m
        Ef = sum(m.E(T) * f for m, f in self.inclusions) / phi
        Em, xi = self.matrix.E(T), 2.0
        eta = (Ef / Em - 1) / (Ef / Em + xi)
        return Em * (1 + xi * eta * phi) / (1 - eta * phi)

    def alpha(self, T):
        ph = self._phases()
        w = np.array([m.E(T) * f for m, f in ph])
        a = np.array([m.alpha(T) for m, _ in ph])
        return (w[:, None] * a).sum(axis=0) / w.sum()

    def Q(self, T):
        E, nu = self.E(T), self.nu
        c = E / (1 - nu ** 2)
        return np.array([[c, nu * c, 0], [nu * c, c, 0], [0, 0, E / (2 * (1 + nu))]])

    def shrinkage_strain(self, T):
        """Equivalent in-plane linear cure-shrinkage strain of the composite (negative)."""
        eps = getattr(self.matrix, "cure_shrinkage", 0.0)
        if eps == 0:
            return 0.0
        return -eps * self.matrix.E(T) * self.phi_m / sum(m.E(T) * f for m, f in self._phases())
