from flask import Flask, request, jsonify
import joblib
import pandas as pd
import os

app = Flask(__name__)

# Memuat model dan scaler yang telah disimpan
model_path = os.path.dirname(os.path.abspath(__file__))
scaler_file = os.path.join(model_path, 'scaler.pkl')
model_file = os.path.join(model_path, 'kmeans_model.pkl')

# Memuat model dan scaler dengan penanganan kesalahan
try:
    scaler = joblib.load(scaler_file)
    kmeans = joblib.load(model_file)
except FileNotFoundError as e:
    print(f"Error loading model files: {e}")
    scaler = None
    kmeans = None

# Memilih fitur yang digunakan untuk segmentasi pelanggan
features = ['Gender', 'Age', 'Annual Income ($)', 'Spending Score (1-100)', 'Work Experience', 'Family Size']
# Tambahkan kolom untuk one-hot encoding profesi
sample_data = pd.read_csv(os.path.join(model_path, 'Customers.csv'))
sample_data = pd.get_dummies(sample_data, columns=['Profession'])
additional_features = [col for col in sample_data.columns if col.startswith('Profession_')]
features += additional_features

# Fungsi untuk pra-pemrosesan dan segmentasi data pelanggan
def preprocess_and_segment(new_data):
    new_data['Gender'] = new_data['Gender'].map({'Male': 0, 'Female': 1})
    new_data = pd.get_dummies(new_data, columns=['Profession'])

    for col in features:
        if col not in new_data.columns:
            new_data[col] = 0
    
    new_data_scaled = scaler.transform(new_data[features])
    clusters = kmeans.predict(new_data_scaled)
    new_data['Cluster'] = clusters
    return new_data

# Fungsi untuk memberikan deskripsi segmen berdasarkan cluster
def segment_description(cluster):
    descriptions = {
        0: "Pelanggan dengan pendapatan rendah dan skor pengeluaran tinggi, kebanyakan berusia 20-30 tahun.",
        1: "Pelanggan dengan pendapatan tinggi, pengalaman kerja panjang, dan usia 30-50 tahun.",
        2: "Pelanggan dengan pendapatan moderat, skor pengeluaran rendah sampai moderat, dan usia 40-60 tahun.",
        3: "Pelanggan dengan pendapatan sangat tinggi, skor pengeluaran sangat tinggi, dan usia bervariasi."
    }
    return descriptions.get(cluster, "Segmen tidak dikenal.")

# Endpoint untuk memeriksa status server
@app.route('/', methods=['GET'])
def status():
    response = {
        "status": "Server is running",
        "code": 200,
        "error": "false",
        "data": {
            "model": "KMeans Segmentation",
            "features": features
        }
    }
    return jsonify(response)

# Endpoint untuk segmentasi pelanggan
@app.route('/segment', methods=['POST'])
def segment_customers():
    if scaler is None or kmeans is None:
        return jsonify({"error": "Model files not loaded properly"}), 500

    customer_data = request.json
    customer_df = pd.DataFrame(customer_data)
    segmented_customers = preprocess_and_segment(customer_df)
    
    # Menambahkan deskripsi segmen
    segmented_customers['Segment_Description'] = segmented_customers['Cluster'].apply(segment_description)
    
    # Mengembalikan hasil dalam format yang diinginkan
    result = segmented_customers.to_dict(orient='records')
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=3000)
