"""The numpy network of scb_ivr.extensions.ml_cnn written in PyTorch (extension ml_torch_port). The same layer specs
build a torch.nn.Sequential; the loss, the Adam settings, the gradient clipping and the early stopping are those of
ml_cnn.Sequential.fit, so a run here can be compared with a numpy run number for number. What changes: autograd
derives the gradients that ml_cnn's backward methods write out by hand, and the library's compiled kernels do the
arithmetic.

Layer by layer (tensors are (samples, channels, time) in both):
  conv     nn.Conv1d(c_in, c_out, k, padding=k // 2)   the same sum, the same weight shape (c_out, c_in, k)
  dense    nn.Linear(n_in, n_out)                       weight is (n_out, n_in): ml_cnn's W transposed
  pool     nn.AvgPool1d(2)                              mean of non-overlapping pairs, an odd last sample dropped
  relu     nn.ReLU()            flatten  nn.Flatten()   (channels, time) -> one axis, row-major as numpy's reshape
  tanh     nn.Tanh()            up       nn.Upsample(scale_factor=2)   each sample repeated twice (A147's decoder)
  unflatten [c, t]  nn.Unflatten(1, (c, t))            one axis -> (channels, time)
A199 checked conv / relu / pool / flatten / dense, A200 the rest.

Needs torch, which the rest of the repository does not: this module stays in the extension's folder, not in
src/scb_ivr, and nothing outside the extension imports it.
"""
from __future__ import annotations

import copy

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


def build_model(specs, seed=0, dtype=torch.float64):
    """ml_cnn layer specs -> nn.Sequential, initialised from ml_cnn's distributions (not its random numbers):
    conv weights N(0, 2 / (c_in k)), dense weights N(0, 1 / n_in), biases 0."""
    gen = torch.Generator().manual_seed(seed)                      # a private random stream: the seed fixes the weights
    layers = []
    for kind, *a in specs:
        if kind == "conv":
            c_in, c_out, k = a
            lay = nn.Conv1d(c_in, c_out, k, padding=k // 2)        # zero-pads k // 2 on both sides: length is kept
            nn.init.normal_(lay.weight, 0.0, (2.0 / (c_in * k)) ** 0.5, generator=gen)    # replaces the default init
            nn.init.zeros_(lay.bias)
        elif kind == "dense":
            n_in, n_out = a
            lay = nn.Linear(n_in, n_out)
            nn.init.normal_(lay.weight, 0.0, (1.0 / n_in) ** 0.5, generator=gen)
            nn.init.zeros_(lay.bias)
        elif kind in ("relu", "pool", "flatten", "tanh", "up"):
            lay = {"relu": nn.ReLU(), "pool": nn.AvgPool1d(2), "flatten": nn.Flatten(), "tanh": nn.Tanh(),
                   "up": nn.Upsample(scale_factor=2, mode="nearest")}[kind]
        elif kind == "unflatten":
            lay = nn.Unflatten(1, tuple(a))                        # (n, c * t) -> (n, c, t)
        else:
            raise ValueError(f"build_model: layer {kind!r} is not ported")
        layers.append(lay)
    return nn.Sequential(*layers).to(dtype)                        # .to(dtype) converts every parameter


def load_numpy(model, net):
    """Copy the parameters of an ml_cnn.Sequential into the model built from the same specs."""
    with torch.no_grad():                                          # plain copies: autograd must not record them
        for lay_t, lay_n in zip(model, net.layers):
            if isinstance(lay_t, nn.Conv1d):
                lay_t.weight.copy_(torch.from_numpy(lay_n.W))
                lay_t.bias.copy_(torch.from_numpy(lay_n.b))
            elif isinstance(lay_t, nn.Linear):
                lay_t.weight.copy_(torch.from_numpy(lay_n.W.T.copy()))    # (n_in, n_out) -> (n_out, n_in)
                lay_t.bias.copy_(torch.from_numpy(lay_n.b))
    return model


def sse(pred, y):
    """ml_cnn's loss: the square error summed over the outputs, averaged over the samples (for 4 outputs that is
    4 x nn.MSELoss, which also averages over the outputs; the clip at max_norm sees the difference)."""
    return ((pred - y) ** 2).sum() / len(y)


@torch.no_grad()                                                   # no graph is recorded inside: less memory, faster
def predict(model, x, batch=512, device="cpu"):
    """Outputs for the CPU tensor x, in batches, back on the CPU."""
    model.eval()                                                   # evaluation mode (no effect here: no dropout / batch norm)
    dtype = next(model.parameters()).dtype
    return torch.cat([model(x[k:k + batch].to(device, dtype)).cpu() for k in range(0, len(x), batch)])


def loss_of(model, x, y, batch=512, device="cpu"):
    p = predict(model, x, batch, device)
    return float(((p.double() - y.double()) ** 2).sum() / len(x))


def fit(model, x, y, xv, yv, epochs=200, batch=64, lr=1e-3, patience=20, seed=0, max_norm=5.0, device="cpu", log=None):
    """ml_cnn.Sequential.fit in PyTorch: Adam on shuffled minibatches, the global gradient norm clipped at max_norm,
    the parameters of the best validation loss kept, stop after `patience` epochs without improvement.
    x, y, xv, yv are CPU tensors; each batch is moved to the model's device and dtype. Returns [(epoch, train, val)]."""
    model.to(device)
    dtype = next(model.parameters()).dtype
    gen = torch.Generator().manual_seed(seed)
    loader = DataLoader(TensorDataset(x, y), batch_size=batch, shuffle=True, generator=gen)    # reshuffled every epoch
    opt = torch.optim.Adam(model.parameters(), lr=lr)              # defaults betas (0.9, 0.999), eps 1e-8 = ml_nn.Adam
    best, best_state, wait, hist = float("inf"), None, 0, []
    for ep in range(epochs):
        model.train()                                              # training mode
        tl = 0.0
        for xb, yb in loader:
            xb, yb = xb.to(device, dtype), yb.to(device, dtype)
            opt.zero_grad()                                        # gradients add up across backward() calls unless cleared
            loss = sse(model(xb), yb)                              # forward pass; autograd records the graph
            loss.backward()                                        # fills p.grad for every parameter
            nn.utils.clip_grad_norm_(model.parameters(), max_norm)    # rescales all gradients if their joint norm > max_norm
            opt.step()                                             # the Adam update from p.grad
            tl += loss.item() * len(xb)                            # .item(): one-element tensor -> Python float
        vl = loss_of(model, xv, yv, device=device)
        hist.append((ep, tl / len(x), vl))
        if log:
            log(f"epoch {ep}: train {tl / len(x):.5f}, val {vl:.5f}")
        if vl < best - 1e-9:
            best, wait, best_state = vl, 0, copy.deepcopy(model.state_dict())    # state_dict: name -> parameter tensor
        else:
            wait += 1
            if wait >= patience:
                break
    if best_state is None:
        raise FloatingPointError("fit: no finite validation loss (non-finite inputs or divergence)")
    model.load_state_dict(best_state)
    return hist
