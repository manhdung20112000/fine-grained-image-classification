import torch
import torch.nn as nn
import torch.nn.functional as F

from torchvision import models


features = 2048
fmap_size = 7


class BCNN(nn.Module):
    def __init__(self, fine_tune=False):
        
        super(BCNN, self).__init__()
        
        resnet = models.resnet50(pretrained=True)
        
        # freezing parameters
        if not fine_tune:
            
            for param in resnet.parameters():
                param.requires_grad = False
        else:
            
            for param in resnet.parameters():
                param.requires_grad = True

        layers = list(resnet.children())[:-2]
        self.features = nn.Sequential(*layers).cuda()

        self.fc = nn.Linear(features ** 2, 120)
        self.dropout = nn.Dropout(0.5)
        
        # Initialize the fc layers.
        nn.init.xavier_normal_(self.fc.weight.data)
        
        if self.fc.bias is not None:
            torch.nn.init.constant_(self.fc.bias.data, val=0)
        
    def forward(self, x):
        
        ## X: bs, 3, 256, 256
        ## N = bs
        N = x.size()[0]
        
        ## x : bs, 1024, 14, 14
        x = self.features(x)
        
        # bs, (1024 * 196) matmul (196 * 1024)
        x = x.view(N, features, fmap_size ** 2)
        x = self.dropout(x)
        
        # Batch matrix multiplication
        x = torch.bmm(x, torch.transpose(x, 1, 2))/ (fmap_size ** 2) 
        x = x.view(N, features ** 2)
        x = torch.sqrt(x + 1e-5)
        x = F.normalize(x)
        
        x = self.dropout(x)
        x = self.fc(x)
        
        return x


if __name__ == '__main__':
    model = BCNN()
    print(model)