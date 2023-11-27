import pickle
import pandas as pd


def predict_tornado(data):
    try:
        pkl_filename = "prediction-tornado.pkl"
        with open(pkl_filename, 'rb') as f_in:
            model = pickle.load(f_in)

        if type(data) == dict:
            df = pd.DataFrame(data, index=[0])
            print(df)
        else:
            df = data

        # probability predictions on the data
        probabilities = model.predict_proba(df)
        y_pred_probabilities = probabilities[:, 1]
        y_pred_percentages = y_pred_probabilities * 100

        # binary predictions
        y_pred = model.predict(df)

        if y_pred == 0:
            return {'predict': 'Non', 'proba': y_pred_percentages[0]}
        elif y_pred == 1:
            return {'predict': 'Tornado', 'proba': y_pred_percentages[0]}

    except Exception as e:
        return {'error': str(e)}

    return {'predict': 'Unknown', 'proba': 0}
