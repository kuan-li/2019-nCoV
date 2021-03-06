import torch
import pickle
import torchvision
import torchvision.datasets as dset
from   torchvision      import transforms
from   dataset          import Dataset
from   torch.utils.data import DataLoader
from   torch.autograd   import Variable
import matplotlib.pyplot as plt
from   model            import SiameseNet
import time
import numpy            as np
import gflags 
import sys
from   collections      import deque
import os
from   tqdm import tqdm
from utils import *

if __name__ == '__main__':

    Flags = gflags.FLAGS
    gflags.DEFINE_bool("cuda", False, "use cuda")
    ############################################
    gflags.DEFINE_string("train_path", "/Users/nicolosavioli/Desktop/nCoV_dataset/train", "training folder")
    gflags.DEFINE_string("test_path", "/Users/nicolosavioli/Desktop/nCoV_dataset/test", 'path of testing folder')
    gflags.DEFINE_string("valid_path", "/Users/nicolosavioli/Desktop/nCoV_dataset/valid", 'path of testing folder')
    ############################################
    gflags.DEFINE_string("save_folder", "/Users/nicolosavioli/Desktop", 'path of testing folder')
    ############################################
    gflags.DEFINE_integer("workers", 4, "number of dataLoader workers")
    gflags.DEFINE_integer("batch_size", 10, "number of batch size")
    gflags.DEFINE_float  ("lr", 0.001, "learning rate")
    gflags.DEFINE_integer("valid_every", 1, "valid model after each test_every iter.")
    gflags.DEFINE_integer("max_iter", 40, "number of iteration - n epoch are max_iter/batch_size")
    

    gflags.DEFINE_string("gpu_ids", "0", "gpu ids used to train")
    Flags(sys.argv)

    trainSet    = Dataset(Flags.train_path,Flags.test_path,Flags.valid_path,Flags.max_iter,"train")
    trainLoader = DataLoader(trainSet, batch_size=Flags.batch_size, shuffle=False, num_workers=Flags.workers)

    validSet    = Dataset(Flags.valid_path,Flags.test_path,Flags.valid_path,Flags.max_iter,"valid")
    validLoader = DataLoader(validSet, batch_size=Flags.batch_size, shuffle=False, num_workers=Flags.workers)

    loss_BCE    = torch.nn.BCEWithLogitsLoss(size_average=True)
    net         = SiameseNet()

    save_path   = os.path.join(Flags.save_folder,"save_data")
    makeFolder(save_path)
    makeFolder(os.path.join(save_path,"models"))

    # multi gpu
    if Flags.cuda:
        os.environ["CUDA_VISIBLE_DEVICES"] = Flags.gpu_ids
        if len(Flags.gpu_ids.split(",")) > 1:
           net = torch.nn.DataParallel(net)
        net.cuda()
    optimizer = torch.optim.Adam(net.parameters(),lr = Flags.lr )
    optimizer.zero_grad()
    loss_val   = 0
    valid_list = []
    for batch_id, (img1, img2, label) in tqdm(enumerate(trainLoader, 1)):
        print("\n ...Train at epoch " +str(batch_id))
        net.train()
        if batch_id > Flags.max_iter:
            break      
        if Flags.cuda:
            img1, img2, label = Variable(img1.cuda()), Variable(img2.cuda()), Variable(label.cuda())
        else:
            img1, img2, label = Variable(img1), Variable(img2), Variable(label)
        optimizer.zero_grad()
        output    = net.forward(img1, img2)
        loss      = loss_BCE   (output, label)
        loss_val += loss.item  ()
        loss.backward()
        optimizer.step()
        if batch_id % Flags.valid_every == 0:
            net.eval()
            list_err = []
            print("\n ...Valid")
            r, e     = 0, 0
            for _, (valid1, valid2, label_valid) in tqdm(enumerate(validLoader, 1)):
              if Flags.cuda:
                 test1, test2 = valid1.cuda(), valid2.cuda()
              else:
                 test1, test2 = Variable(valid1), Variable(valid2)
              output = net.forward(test1, test2).data.cpu().numpy()
              pred   = np.argmax(output)
              if pred ==1:
                   r += 1
              else:
                   e += 1
              list_err.append(r*1.0/(r+e))
            valid_list.append(np.mean(list_err))
            plot(valid_list,save_path)






















        
    
