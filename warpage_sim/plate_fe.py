"""Kirchhoff plate FE (Bogner-Fox-Schmit C1 rectangles) with unilateral chuck contact
and a progressive vacuum-capture model.

Physics
-------
* Bending energy  1/2 (k - k_nat)^T D* (k - k_nat), k = (w_xx, w_yy, 2 w_xy),
  where k_nat is the free thermal curvature from CLT and D* the reduced bending stiffness.
  (The flattened end-state is flat, so a linear bending model is exact there; the path is
  approximate for very large warpage.)
* Gravity acts on the whole panel; the chuck is the rigid plane w = 0 (w >= 0).
* Vacuum capture: suction pressure p acts only on elements whose gap to the chuck is below
  the capture gap g_cap (region the vacuum holes/grooves can evacuate). Captured elements stay
  captured. The loop repeats until the captured region stops growing ("zipping").
* Regions enclosed by a sealed ring (not connected to the outer panel edge) are evacuated too.
* Pass criterion: max gap <= tol over the whole panel.

Quarter model (double symmetry) is used: domain [0, Lx/2] x [0, Ly/2], with the mesh graded
toward the free edges where the lift-off zone is short (length ~ sqrt(2 D k / p)).
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy import ndimage

G = 9.81


def _hermite(xi, h):
    N = np.array([1 - 3*xi**2 + 2*xi**3, h*(xi - 2*xi**2 + xi**3), 3*xi**2 - 2*xi**3, h*(-xi**2 + xi**3)])
    dN = np.array([-6*xi + 6*xi**2, h*(1 - 4*xi + 3*xi**2), 6*xi - 6*xi**2, h*(-2*xi + 3*xi**2)]) / h
    d2N = np.array([-6 + 12*xi, h*(-4 + 6*xi), 6 - 12*xi, h*(-2 + 6*xi)]) / h**2
    # node 0 -> (value, slope) = (N[0], N[1]); node 1 -> (N[2], N[3])
    return N, dN, d2N


LOCAL_NODES = [(0, 0), (1, 0), (1, 1), (0, 1)]


def _element_shape(xi, eta, hx, hy):
    Nx, dNx, d2Nx = _hermite(xi, hx)
    Ny, dNy, d2Ny = _hermite(eta, hy)
    n = np.zeros(16); wxx = np.zeros(16); wyy = np.zeros(16); wxy = np.zeros(16)
    for a, (i, j) in enumerate(LOCAL_NODES):
        for k, (sx, sy) in enumerate([(0, 0), (1, 0), (0, 1), (1, 1)]):
            ix, iy = 2*i + sx, 2*j + sy
            idx = 4*a + k
            n[idx] = Nx[ix] * Ny[iy]
            wxx[idx] = d2Nx[ix] * Ny[iy]
            wyy[idx] = Nx[ix] * d2Ny[iy]
            wxy[idx] = dNx[ix] * dNy[iy]
    return n, np.vstack([wxx, wyy, 2*wxy])


def graded_nodes(a, n, edge_bias=0.85):
    """Node coordinates on [0, a], refined toward the free edge x = a where lift-off occurs."""
    s = np.linspace(0, 1, n + 1)
    return a * ((1 - edge_bias) * s + edge_bias * np.sin(np.pi * s / 2))


class QuarterPlate:
    def __init__(self, Lx, Ly, Dstar, k_nat, areal_mass, nx=40, ny=None, edge_bias=0.85):
        ny = ny or nx
        self.nx, self.ny = nx, ny
        self.ax, self.ay = Lx/2, Ly/2
        self.xs = graded_nodes(self.ax, nx, edge_bias)
        self.ys = graded_nodes(self.ay, ny, edge_bias)
        gp, gw = np.polynomial.legendre.leggauss(4)
        gp = (gp + 1)/2; gw = gw/2
        shp = [[_element_shape(xi, eta, 1.0, 1.0) for eta in gp] for xi in gp]

        sub = (np.arange(4) + 0.5) / 4

        def subsample(hx, hy):
            return np.array([_element_shape(xi, eta, hx, hy)[0] for xi in sub for eta in sub])

        def element(hx, hy):
            Ke = np.zeros((16, 16)); fT = np.zeros(16); fq = np.zeros(16)
            # scale unit-size shape functions: slope dofs ~ h, 2nd derivatives ~ 1/h^2
            S = np.ones(16); S[1::4] = hx; S[2::4] = hy; S[3::4] = hx*hy
            for i, (xi, wi) in enumerate(zip(gp, gw)):
                for j, (eta, wj) in enumerate(zip(gp, gw)):
                    n, Bm = _element_shape(xi, eta, hx, hy)
                    dA = wi*wj*hx*hy
                    Ke += Bm.T @ Dstar @ Bm * dA
                    fT += Bm.T @ Dstar @ k_nat * dA
                    fq += n * dA
            return Ke, fT, fq

        nn = (nx+1)*(ny+1); self.ndof = 4*nn
        node = lambda ix, iy: ix*(ny+1) + iy
        edofs, Ks, fTs, fqs, areas, Nsubs = [], [], [], [], [], []
        cache = {}
        for ex in range(nx):
            for ey in range(ny):
                hx, hy = self.xs[ex+1]-self.xs[ex], self.ys[ey+1]-self.ys[ey]
                key = (round(hx, 12), round(hy, 12))
                if key not in cache:
                    cache[key] = element(hx, hy) + (subsample(hx, hy),)
                Ke, fT, fq, Ns = cache[key]
                Nsubs.append(Ns)
                ns = [node(ex+i, ey+j) for (i, j) in LOCAL_NODES]
                edofs.append([4*m + k for m in ns for k in range(4)])
                Ks.append(Ke); fTs.append(fT); fqs.append(fq); areas.append(hx*hy)
        self.edofs = np.array(edofs)
        self.area_e = np.array(areas)
        self.Nsub = np.array(Nsubs)  # (ne, 16 sub-points, 16 dofs)
        rows = np.repeat(self.edofs, 16, axis=1).ravel()
        cols = np.tile(self.edofs, (1, 16)).ravel()
        K = sp.csr_matrix((np.array(Ks).ravel(), (rows, cols)), shape=(self.ndof, self.ndof))
        self.wdof = 4*np.arange(nn)
        # tiny elastic foundation to remove the rigid translation when nothing touches
        kscale = np.abs(K.diagonal()[self.wdof]).max()
        K = K + sp.diags(np.where(np.arange(self.ndof) % 4 == 0, kscale*1e-12, 0.0))
        self.K = K.tocsr()
        # np.bincount instead of np.add.at (broadcasting add.at is unreliable in some numpy builds)
        self.fT = np.bincount(self.edofs.ravel(), weights=np.array(fTs).ravel(), minlength=self.ndof)
        self.fq_e = np.array(fqs)  # element load vectors for unit upward pressure
        self.q_grav = -areal_mass*G
        # symmetry constraints: x=0 -> w_x = w_xy = 0 ; y=0 -> w_y = w_xy = 0
        fixed = []
        for iy in range(ny+1):
            m = node(0, iy); fixed += [4*m+1, 4*m+3]
        for ix in range(nx+1):
            m = node(ix, 0); fixed += [4*m+2, 4*m+3]
        self.sym_fixed = np.unique(fixed)
        self.node_xy = np.array([[x, y] for x in self.xs for y in self.ys])
        self.enodes = self.edofs[:, ::4] // 4

    def load(self, p_elem):
        """p_elem: downward suction per element (Pa)."""
        f = self.fT.copy()
        qe = self.q_grav - p_elem
        f += np.bincount(self.edofs.ravel(), weights=(qe[:, None]*self.fq_e).ravel(), minlength=self.ndof)
        return f

    def solve_contact(self, f, active=None, max_iter=200):
        nn = len(self.wdof)
        active = np.zeros(nn, bool) if active is None else active.copy()
        tol_w = 1e-9
        for _ in range(max_iter):
            fixed = np.unique(np.concatenate([self.sym_fixed, self.wdof[active]]))
            free = np.setdiff1d(np.arange(self.ndof), fixed)
            u = np.zeros(self.ndof)
            u[free] = spla.spsolve(self.K[free][:, free].tocsc(), f[free])
            w = u[self.wdof]
            r = (self.K @ u - f)[self.wdof]   # chuck reaction (>0 pushes up)
            pen = (~active) & (w < -tol_w)
            pull = active & (r < -1e-9*np.abs(f).max())
            if not pen.any() and not pull.any():
                return u, active
            # primal-dual active-set update: add penetrating nodes and release tensile ones together
            active = (active & ~pull) | pen
        return u, active

    def gaps_sub(self, u):
        """Gap at 4x4 sub-points of every element (Hermite interpolation)."""
        return np.einsum("eqd,ed->eq", self.Nsub, u[self.edofs])

    def _enclosed(self, frac):
        """Regions fully surrounded by sealed elements and cut off from the panel's outer edge
        are evacuated through the chuck holes as well -> captured."""
        sealed = (frac >= 0.999).reshape(self.nx, self.ny)
        lab, n = ndimage.label(~sealed)
        if n == 0:
            return frac
        outer = np.unique(np.concatenate([lab[-1, :], lab[:, -1]]))  # x = Lx/2, y = Ly/2 edges
        enclosed = (~np.isin(lab, outer)) & (lab > 0)
        out = frac.copy()
        out[enclosed.ravel()] = 1.0
        return out

    def chuck(self, p_vac, g_cap, ramp=(0.05, 0.15, 0.35, 0.65, 1.0), leak_beta=0.0):
        """Simulate placement under gravity, then vacuum build-up with capture/zipping.

        Each element carries a captured area fraction (share of its 4x4 sub-points whose gap
        is <= g_cap); suction on the element is the plenum pressure times that fraction.
        Capture never reverts. The vacuum is built up in steps (ramp) as in a real chuck.

        Leak model: chuck surface not covered by a captured panel region leaks air into the
        plenum, so the achievable plenum vacuum is
            p_plenum = p_supply / (1 + leak_beta * f_open),   f_open = uncaptured area fraction.
        leak_beta = (open-chuck conductance)/(pump conductance), an equipment constant to be
        calibrated (0 = ideal, no leak; porous chucks without zone valves: ~5-50).
        """
        ne = len(self.edofs)
        A = self.area_e
        frac = np.zeros(ne)
        u, active = self.solve_contact(self.load(np.zeros(ne)), np.ones(len(self.wdof), bool))
        u_placed = u.copy()
        p_pl = 0.0
        for stage in ramp:
            for it in range(4*ne):
                new = self._enclosed(np.maximum(frac, (self.gaps_sub(u) <= g_cap).mean(axis=1)))
                f_open = 1.0 - (A*new).sum()/A.sum()
                p_new = p_vac*stage/(1.0 + leak_beta*f_open)
                if it > 0 and np.abs(new - frac).max() < 1e-12 and abs(p_new - p_pl) < 1e-9*p_vac:
                    break
                frac, p_pl = new, p_new
                u, active = self.solve_contact(self.load(p_pl*frac), active)
        f_open = 1.0 - (A*frac).sum()/A.sum()
        return {"w": u[self.wdof], "w_placed": u_placed[self.wdof], "captured": frac,
                "max_gap": max(u[self.wdof].max(), self.gaps_sub(u).max()),
                "p_plenum": p_vac/(1.0 + leak_beta*f_open), "f_open": f_open}

    def required_pressure(self, g_cap, tol, p_max=1e6, rel=0.03, leak_beta=0.0):
        """Lowest supply vacuum giving full contact: ascending scan, then bisection."""
        ok = lambda p: self.chuck(p, g_cap, leak_beta=leak_beta)["max_gap"] <= tol
        lo, hi = 0.0, None
        p = 500.0
        while p <= p_max:
            if ok(p):
                hi = p
                break
            lo, p = p, p*2
        if hi is None:
            return np.inf
        while hi - lo > max(rel*hi, 50.0):
            mid = 0.5*(lo + hi)
            if ok(mid):
                hi = mid
            else:
                lo = mid
        return hi

    def full_field(self, wq):
        """Mirror the quarter nodal field to the full panel grid (for plotting)."""
        W = wq.reshape(self.nx+1, self.ny+1)          # [ix, iy]
        Wx = np.vstack([W[::-1][:-1], W])
        Wf = np.hstack([Wx[:, ::-1][:, :-1], Wx])
        x = np.concatenate([-self.xs[::-1][:-1], self.xs])
        y = np.concatenate([-self.ys[::-1][:-1], self.ys])
        return x, y, Wf
