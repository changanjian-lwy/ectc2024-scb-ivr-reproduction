"""The forward pass of scb_ivr.extensions.ml_nn.MLP on PyTorch tensors (extension ml_torch_port): tanh hidden layers,
the output's pre-activation returned. The weights stay in ml_nn's shapes (W is (n_in, n_out), x @ W + b), so a numpy
network's arrays are used as they are. With the tensors created by tensors(net, grad=True), autograd gives the
gradients of any loss with respect to the weights; with an input that requires grad, it gives the gradient with
respect to the input, which ml_nn does not provide (A202: design search through a surrogate).

Needs torch: like torch_cnn.py, it stays in the extension's folder.
"""
from __future__ import annotations

import numpy as np
import torch


def tensors(net, grad=False):
    """(Ws, bs): float64 copies of an ml_nn.MLP's weights and biases."""
    mk = lambda a: torch.tensor(np.asarray(a, dtype=float), requires_grad=grad)
    return [mk(a) for a in net.W], [mk(a) for a in net.b]


def forward(Ws, bs, x):
    for i, (w, b) in enumerate(zip(Ws, bs)):
        x = x @ w + b
        if i < len(Ws) - 1:
            x = torch.tanh(x)
    return x
