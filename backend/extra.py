import pickle

with open("rmodel.pkl", "wb") as f:
    pickle.dump(model, f)
