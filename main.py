import numpy as np
from pathlib import Path
import torch
from torch import cuda
from torch.utils.data import DataLoader

from pytorch_dataset import MyMultitaskDataset
from Model.model_training import trainModel
from Model.model import MultitaskCNN
from Model.model_evaluate import evaluate
from Model.config import model_cfg
from utils import *




def main(mainPath:str,  modelPath:str, batchSize:int, numFolds:int=6)->None:
    """
    Trains, evaluates, and stores the best model for each fold of a k-fold cross-validation.

    Args:
        mainPath (str): Path to the parent directory containing the subject folders.
        modelPath (str): Location to save the best model from each fold.
        batchSize (int): Number of samples in a batch.
        numFolds (int): Number of folds to use for cross-validation. Default: 6.
    """
   
    # Store  accuracy from each CV
    cv_accuracy_digit = []
    cv_accuracy_gender = []

    # Store predicton from each CV (this is for confusion matrix)
    prediction_cv = []

    # Start training under Cross-validation (CV)
    for k in range(numFolds):
        print(f'Fold-{k+1} is processing....')

        # Get each CV splits train, val and test folder paths
        train_dirs, val_dirs, test_dirs = cvFolderSplits(mainPath=mainPath, 
                                                         k=k, 
                                                         num_folds=numFolds)

        
        # Custom Dataset and Data loader for Training
        train_dataset = MyMultitaskDataset(train_dirs)
        print(f'Total train samples: {train_dataset.__len__()}')
        trainDataloader = DataLoader(train_dataset, batch_size=batchSize, shuffle=True, drop_last=True)
        
        # Custom Dataset and Data loader for Validation
        val_dataset = MyMultitaskDataset(val_dirs)
        print(f'Total val samples: {val_dataset.__len__()}')
        valDataloader = DataLoader(val_dataset, batch_size=batchSize, shuffle=True, drop_last=True)

        # Custom Dataset and Data loader for Testing
        test_dataset = MyMultitaskDataset(test_dirs)
        print(f'Total test samples: {test_dataset.__len__()}')
        testDataloader = DataLoader(test_dataset, batch_size=batchSize, shuffle=True, drop_last=True)
        print()
        

        # Start Training model
        trainModel(trainData=trainDataloader,
                   valData=valDataloader, 
                   fold=k+1)
        

        # Evaluate on test data
        model = MultitaskCNN() # Initialize model
        model.load_state_dict(torch.load(f'{modelPath}/best_model_{k+1}.pth', 
                                         map_location=torch.device( model_cfg['device']))) # Load the best model weight
        model.to(device) # Specify device
        predict = evaluate(model,testDataloader, device) # Predict
        prediction_cv.append({'fold_'+ str(k+1):predict}) # store prediction
        cv_accuracy_digit.append(predict['accuracy_digit']) # Get digit accuracy and store
        cv_accuracy_gender.append(predict['accuracy_gender']) # Get gender accuracy and store
    
    # Save Prediction results from all folds
    savePrediction(prediction_cv, modelPath)

    # Print average accuracy from CV
    print(f'Avearge cv_accuracy_digit:  {np.array(cv_accuracy_digit).mean(): .3f}')
    print(f'Avearge cv_accuracy_gender:  {np.array(cv_accuracy_gender).mean(): .3f}')


if __name__ == "__main__":

    # Check if CUDA is available, else use CPU
    device = model_cfg['device']
    print(f'Process on {device}', end='\n\n')
    
    # This need to replace as per your folder structures
    mainPath = 'Data/Processed'
    modelPath = model_cfg['best_model_path'] # best model location
    numFolds = model_cfg['num_folds'] # fold size
    batch_size = model_cfg['batch_size'] # fold size

    # Start training model
    main(mainPath=mainPath, 
         modelPath=modelPath, 
         batchSize=batch_size,
         numFolds=numFolds)
    
   

