# KNN Model Implementation

This project implements a K-Nearest Neighbors (KNN) model for classification or regression tasks. The implementation includes data preprocessing, model training, evaluation, and visualization.

## Project Structure

```
SisaRasa/
├── data/              # Directory for datasets
├── models/            # Directory for saved models and visualizations
└── src/               # Source code
    ├── data_preprocessing.py  # Data preprocessing functions
    ├── knn_model.py           # KNN model implementation
    └── main.py                # Main script to run the model
```

## Getting Started

### Prerequisites

Make sure you have the following Python packages installed:

```
numpy
pandas
scikit-learn
matplotlib
seaborn
```

You can install them using pip:

```
pip install numpy pandas scikit-learn matplotlib seaborn
```

### Dataset Placement

1. Place your dataset file (CSV, Excel) in the `data/` directory.
2. Make sure your dataset has a target column (the variable you want to predict).

### Running the Model

Navigate to the `src/` directory and run the `main.py` script:

```
cd src
python main.py --data_path "../data/your_dataset.csv" --target_column "target_column_name"
```

#### Command Line Arguments

- `--data_path`: Path to the dataset file (required)
- `--target_column`: Name of the target column in the dataset (required)
- `--task`: Type of task: 'classification' or 'regression' (default: 'classification')
- `--test_size`: Proportion of the dataset to include in the test split (default: 0.2)
- `--n_neighbors`: Number of neighbors to use for KNN (default: 5)
- `--find_optimal_k`: Whether to find the optimal number of neighbors (flag)
- `--save_model`: Whether to save the trained model (flag)
- `--model_path`: Path to save the trained model (default: 'models/knn_model.pkl')

### Example

For a classification task with a dataset named 'iris.csv' and a target column named 'species':

```
python main.py --data_path "../data/iris.csv" --target_column "species" --find_optimal_k --save_model
```

For a regression task:

```
python main.py --data_path "../data/housing.csv" --target_column "price" --task regression --find_optimal_k --save_model
```

## Features

- Data preprocessing (handling missing values, encoding categorical features)
- Automatic feature scaling
- Finding the optimal number of neighbors (k)
- Model evaluation with various metrics
- Confusion matrix visualization for classification tasks
- Model saving and loading

## Output

- Evaluation metrics will be printed to the console
- For classification tasks, a confusion matrix will be saved to 'models/confusion_matrix.png'
- If `--find_optimal_k` is specified, a plot of error rates vs. number of neighbors will be saved to 'models/optimal_k.png'
- If `--save_model` is specified, the trained model will be saved to the specified path (default: 'models/knn_model.pkl')
