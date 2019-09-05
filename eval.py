import argparse
import numpy as np
import matplotlib.pylab as plt
import sys
import pandas as pd
import sklearn, sklearn.model_selection, sklearn.neighbors
import sklearn.linear_model
import gzip
import utils
import encoders
import collections
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument('embeddings_file', help='File with embeddings')
parser.add_argument('-num_examples', nargs='?', type=int, default=20000, help='')
parser.add_argument('-num_trials', nargs='?', type=int, default=10, help='')
parser.add_argument('-labels_file', nargs='?', default="test_labels.csv.gz", help='')
parser.add_argument('-model', type=str, default="knn", choices=["knn","lr","adaboost"],help='Model to evaluate embeddings with.')
parser.add_argument('-encode_method', type=str, default=None, choices=[o for o in dir(encoders) if not o.startswith("_")], help='to encode the signals on the fly')
args = parser.parse_args()

print(args)

enc = None
if args.encode_method != None:
    enc = getattr(encoders, args.encode_method)()
    print("Encoder:",enc)

## get counts
lines_emb = 0
with gzip.open(args.embeddings_file, 'rb') as f:
    for line in f:
        lines_emb += 1

lines_labels = 0
with gzip.open(args.labels_file, 'rb') as f:
    for line in f:
        lines_labels += 1

print("lines_emb:", lines_emb)

if lines_labels != lines_emb:
    print(" !! Issue with coverage of labels. The data must align to the labels.")
    sys.exit()


def evaluate(num_examples, num_trials, label_type):
    
    all_acc = []
    for i in range(num_trials):
        
        print("Generating subset", i)
        
        data, labels = utils.getSubset(num_examples, embeddings_file=args.embeddings_file, seed=i)
        
        # remove class 0 from btype
        data = data[labels["btype"] != 0]
        labels = labels[labels["btype"] != 0]
        
        # remove class 0 from rtype
        data = data[labels["rtype"] != 0]
        labels = labels[labels["rtype"] != 0]
        
        # remove class 1 from rtype
        data = data[labels["rtype"] != 1]
        labels = labels[labels["rtype"] != 1]
        
        # remove class 2 from rtype
        data = data[labels["rtype"] != 2]
        labels = labels[labels["rtype"] != 2]
        
        if enc:
            newdata = []
            for emb in tqdm(data.values):
                newdata.append(enc.encode(emb))
            data = np.asarray(newdata)
        
        print(collections.Counter(labels[label_type]))

        X, X_test, y, y_test = \
            sklearn.model_selection.train_test_split(data, labels[label_type], 
                                                     train_size=len(labels)//2, 
                                                     test_size=len(labels)//2, 
                                                     stratify=labels[label_type],
                                                     random_state=i)
        print("X", X.shape, "X_test", X_test.shape)
        if args.model == "knn":
            model = sklearn.neighbors.KNeighborsClassifier(n_neighbors=3)
        elif args.model == "lr":
            model = sklearn.linear_model.LogisticRegression(multi_class="auto")
        elif args.model == "adaboost":
            model = sklearn.ensemble.AdaBoostClassifier()
        else:
            print("Unknown model")
            sys.exit();
            
        print(model)
        model = model.fit(X, y.values.flatten())
        y_pred = model.predict(X_test)
        bacc = sklearn.metrics.balanced_accuracy_score(y_test.values.flatten(),y_pred)
        all_acc.append(bacc)
        
        print("   Run {}".format(i) + ", label_type: {}".format(label_type) + ", Balanced Accuracy: {}".format(bacc)) 

    return np.asarray(all_acc).mean(), np.asarray(all_acc).std()
    
    
    
btype_mean,btype_stdev = evaluate(args.num_examples, args.num_trials, "btype")
rtype_mean,rtype_stdev = evaluate(args.num_examples, args.num_trials, "rtype")

print("btype, Balanced Accuracy:",round(btype_mean,3), "+-", round(btype_stdev,3), "num_trials:",args.num_trials, args) 
print("rtype, Balanced Accuracy:",round(rtype_mean,3), "+-", round(rtype_stdev,3), "num_trials:",args.num_trials, args) 

    
    
    
    
    
    
