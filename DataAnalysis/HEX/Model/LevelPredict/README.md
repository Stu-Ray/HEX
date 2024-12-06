## FT-transformer

In the FT-transformer project, the detailed functions of each folder and file are as follows:

**data**: Stores the model parameters, input data for test sets, training sets, and prediction sets, as well as the corresponding output results required by the project.

- model_param: Specifically used for storing parameter files of the ME_cost and ME_one-hot models.
- predict_result: Stores the expression level results predicted by the ME_cost and ME_one-hot models.
- train_and_test_result: Records the loss values and accuracy results of the ME_cost and ME_one-hot models during the training and testing processes.

**images**: Stores the loss and accuracy curve images that change with the number of training epochs during model training and testing.

**model**: Contains Python files related to the model.

- ft_transformer: Responsible for the creation and initialization of the model.
- model_func: Contains the training and testing functions of the model, as well as custom loss functions (such as Focal Loss).

**preprocess**: Stores Python files related to dataset preprocessing.

- preprocess_data_cost/one-hot: Converts training and testing datasets into the format required by the ME_cost/ME_one-hot models and removes redundant information features.
- preprocess_predict_data_cost/one-hot: Converts prediction datasets into the format required by the ME_cost/ME_one-hot models and removes redundant information features.

**utils**: Contains Python files for utility classes, which assist in various tasks within the project.

- Aggregate: Responsible for matching the predicted levels of all expressions with operators.
- category: Stores workload and operator type information to facilitate conversion into numerical representations ranging from 0 to category-1.
- tpch_sql: Provides functionality to convert SQL statements into corresponding SQL marker bits.

**cost/onehot-train_and_test**: The main function for training and testing the ME_cost and ME_one-hot models, responsible for executing the training and testing processes.

**predict_cost/onehot_result**: The main function for predictions using the ME_cost and ME_one-hot models, responsible for executing prediction tasks and outputting results.

<br/>

<br/>

<br/>

<br/>

   We employ the FT-transformer as a model for predicting expression levels. Its input consists of expression-related information, which is divided into two categories: categorical variables and numerical variables. Categorical variables primarily include information about the expression, the type of operator it belongs to, and other relevant details. Numerical variables encompass EEOP information and cost information. The output is the probabilities of four levels for the predicted expression.

   The usage of the FT-transformer is as follows:

```
model = FTTransformer(
    categories=[len(database_categ),len(operator_categ), 23, 106, len(operator_categ),len(operator_categ)],  #The number of features for categorical variables (length), where each number represents the number of categories for the corresponding type of feature.
    num_continuous=x_train_numer.shape[1],  #The number of features for numerical variables.  
    dim=64,     #The dimension of the embedding layer.
    depth=6,    #The number of transformer encoders used.
    heads=4,    #The number of heads in the multi-head attention mechanism.
    dim_out=num_classes, #Output dimension (with 4 levels for expression classification).
    attn_dropout=0.1,  #Dropout rate for multi-head attention.
    ff_dropout=0.1 #Dropout rate for the feedforward neural network.
).to(device)
```

     The usage case is as follows:

```
    model = FTTransformer(
        categories=(10, 5, 6, 5, 8),
        num_continuous=10,
        dim=32,
        dim_out=1,
        depth=6,
        heads=8,
        attn_dropout=0.1,
        ff_dropout=0.1
    )
    x_categ = torch.randint(0, 5, (1, 5), dtype=torch.long) 
    x_numer = torch.randn(1, 10, dtype=torch.float32)  

    pred = model(x_categ, x_numer)
    print(pred)
```

     In this context, it is necessary to ensure that categorical features are converted to corresponding values ranging from 0 to the number of categories minus 1, and that these values are of the long type in torch. Numerical features should be of the float type in torch. Typically, dim is set to 32, depth to 6, heads to 8, and attn_dropout and ff_dropout to 0.1.