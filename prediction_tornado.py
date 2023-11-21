import pickle
import pandas as pd


def predict_tornado(data):
    try:
        # loading the model from the saved file
        pkl_filename = "prediction-tornado.pkl"
        with open(pkl_filename, 'rb') as f_in:
            model = pickle.load(f_in)

        if type(data) == dict:
            df = pd.DataFrame(data, index=[0])
            print(df)
        else:
            df = data

        y_pred = model.predict(df)

        if y_pred == 0:
            return 'Non'
        elif y_pred == 1:
            return 'Tornado'

    except Exception as e:
        return str(e)

    return 'Unknown'
