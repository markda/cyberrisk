import torch.nn as nn


class MLP(nn.Module):

    def __init__(self, n_in, n_hidden, dropout=0.2):
        super(MLP, self).__init__()
        self.linear = nn.Linear(n_in, n_hidden)
        self.activation = nn.LeakyReLU(negative_slope=0.1)
        self.dropout = nn.Dropout(dropout)
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.orthogonal_(self.linear.weight)
        nn.init.zeros_(self.linear.bias)

    def forward(self, x):
        x = self.dropout(x)
        x = self.linear(x)
        x = self.activation(x)
        return x

    
    
