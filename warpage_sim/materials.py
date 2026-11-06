"""Temperature-dependent material models (SI units: Pa, 1/K, kg/m^3, degC)."""
from dataclasses import dataclass
import numpy as np


@dataclass
class Material:
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

    @classmethod
    def from_dict(cls, d):
        units = {"E_glassy": 1e9, "E_rubbery": 1e9, "alpha_x_glassy": 1e-6, "alpha_y_glassy": 1e-6,
                 "alpha_x_rubbery": 1e-6, "alpha_y_rubbery": 1e-6, "allowable_stress": 1e6}
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
