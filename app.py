import pandas as pd
from flask import Flask, request, render_template, redirect, url_for
import boto3
import matplotlib.pyplot as plt
import seaborn as sns

app = Flask(__name__)

# AWS S3 configuration
s3 = boto3.client('s3')
bucket_name = 'data-analysis-visualize'
file_name = 'Pokemons.csv'

# Function to load the uploaded dataset from S3
def load_dataset_from_s3(bucket_name, file_name):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket_name, Key=file_name)
    dataset = pd.read_csv(obj['Body'])
    return dataset

# Function to calculate basic statistics for the dataset
def calculate_basic_statistics(dataset):
    statistics = dataset.describe()
    return statistics

#Function to identify missing values in the dataset
def identify_missing_values(dataset):
    missing_values = dataset.isna().sum()
    return missing_values

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            # Upload the file to S3
            s3.upload_fileobj(file, bucket_name, file.filename)
            return redirect(url_for('data_analysis'))
    return render_template('upload.html')

@app.route('/data_analysis', methods=['GET'])
def data_analysis():
    # Load the dataset and perform analysis
    dataset = load_dataset_from_s3(bucket_name, file_name)
    statistics = calculate_basic_statistics(dataset)
    missing_values = identify_missing_values(dataset)

    # Convert the missing_values Series to a DataFrame
    missing_values_df = pd.DataFrame({'Missing Values': missing_values})

     # Debugging statements
    print(statistics)
    print(missing_values)

    # Render a template or return the data as JSON to display in your web page
    return render_template('data_analysis.html', statistics=statistics.to_html(), missing_values=missing_values_df.to_html())

@app.route('/data-cleaning', methods=['POST'])
def data_cleaning():
    fill_method = request.form['fill_method']
    fill_value = request.form['fill_value']
    drop_threshold = request.form['drop_threshold']

    # Load the dataset
    dataset = load_dataset_from_s3(bucket_name, file_name)

    # Data Cleaning Logic
    if fill_method == 'value':
        # Fill missing values with the specified value
        dataset.fillna(value=fill_value, inplace=True)
    elif fill_method == 'mean':
        # Fill missing values with the mean
        dataset.fillna(dataset.mean(), inplace=True)
    elif fill_method == 'median':
        # Fill missing values with the median
        dataset.fillna(dataset.median(), inplace=True)

         # Convert fill_value and drop_threshold to strings
    fill_value_str = str(fill_value)
    drop_threshold_str = str(drop_threshold)

    # Drop columns with a high percentage of missing values
    drop_threshold = float(drop_threshold)
    threshold = drop_threshold / 100.0
    dataset.dropna(thresh=int(threshold * len(dataset)), axis=1, inplace=True)

    # Calculate statistics and missing values for the cleaned dataset
    statistics = calculate_basic_statistics(dataset)
    missing_values = identify_missing_values(dataset)

     # Convert the missing_values Series to a DataFrame
    missing_values_df = pd.DataFrame({'Missing Values': missing_values})

    # Render the updated data analysis template
    return render_template('data_analysis.html', statistics=statistics.to_html(), missing_values=missing_values_df.to_html(), fill_value=fill_value_str, drop_threshold=drop_threshold_str)

@app.route('/visualize-data', methods=['POST'])
def visualize_data():
     # Load the dataset
    dataset = load_dataset_from_s3(bucket_name, file_name)

       # Get the list of all column names
    columns = dataset.columns.tolist()

    selected_column_x = request.form['selected_column_x']
    selected_column_y = request.form['selected_column_y']
    visualization_type = request.form['visualization_type']

   

    # Data Visualization Logic
    plt.figure(figsize=(10, 6))

    if visualization_type == 'histogram':
        sns.histplot(dataset[selected_column_x], kde=True)
        plt.title(f'Histogram of {selected_column_x}')
    elif visualization_type == 'bar_chart':
        sns.countplot(data=dataset, x=selected_column_x)
        plt.title(f'Bar Chart of {selected_column_x}')
    elif visualization_type == 'scatter_plot':
        if selected_column_x in dataset.columns and selected_column_y in dataset.columns:
            sns.scatterplot(data=dataset, x=selected_column_x, y=selected_column_y)
            plt.title(f'Scatter Plot: {selected_column_x} vs. {selected_column_y}')
        else:
            return "Selected columns do not exist in the dataset."
    elif visualization_type == 'heatmap':
        corr_matrix = dataset.corr()
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm')
        plt.title('Correlation Heatmap')

    # Save the visualization as an image or render it in the web page
    visualization_image = 'path_to_saved_image.png'  # Update with your logic
    plt.savefig(visualization_image)

    # Render the updated data analysis template with the visualization
    return render_template('data_analysis.html', visualization_image=visualization_image, columns=dataset.columns.tolist())

if __name__ == '__main__':
    app.run(debug=True)