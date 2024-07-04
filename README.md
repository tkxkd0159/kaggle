- [Prerequisites](#prerequisites)
  - [Vector Embedding](#vector-embedding)
  - [Model](#model)
  - [Tuning Parameters](#tuning-parameters)
  - [BigQuery SQL](#bigquery-sql)
    - [GoogleSQL](#googlesql)
    - [BigQuery ML SQL](#bigquery-ml-sql)
    - [INFORMATION SCHEMA view](#information-schema-view)
- [Competition List](#competition-list)

# Prerequisites

## Vector Embedding
In the context of machine learning and natural language processing, embeddings are **dense** vector representations (lists of numbers) that capture the meaning and relationships of words, sentences, or other objects. Each element in the vector represents a feature or characteristic of the object.

Think of them as a way to translate something complex (like a piece of text or an image) into a simplified form that a computer can easily understand and work with. The key idea is that similar objects will have similar embeddings, allowing us to measure and compare their relationships using math.

Let's take the word "king" as an example. A word embedding for "king" might look like this. This vector of numbers represents different aspects of the word "king," such as its relation to royalty, power, gender, and so on.
```
[-0.25, 0.31, 0.18, -0.05, ...]
```

* Sentence Embeddings: Similar to word embeddings, but represent entire sentences.
* Image Embeddings: Capture the visual features of images.
* Audio Embeddings: Represent the characteristics of sounds.
* Graph Embeddings: Used to represent nodes and edges in graphs.


**Sparse vs. Dense Vectors**
* Sparse Vector: A common approach is the bag-of-words model. Each element in the vector represents a word, and its value is the count of that word in the document. Most documents won't contain all words from a large vocabulary, resulting in many zeros.
  * Dimensionality: Potentially thousands or tens of thousands, depending on the vocabulary size.
  * Example: [0, 3, 0, 1, 2, 0, ...]

* Dense Vector: You can use techniques like averaging word embeddings or more advanced methods like Doc2Vec to create a dense vector representation for each document.
  * Dimensionality: Typically lower than sparse document vectors, often in the hundreds.
  * Example: [0.15, -0.23, 0.41, ..., 0.08]

## Model
  * `embeddingmodel` : a model to generate text embeddings for tasks like semantic search, information retrieval, or recommendation systems. Not designed for general text generation or understanding tasks
  * clustering model : `cluster_c<chunk-size>_n<n-of-cluster>`
  * `txtbison` (PaLM 2) : a model for a variety of text-based NLP tasks and prioritize language understanding/generation.
  * `gemini-pro10`, `gemini-pro15` : model that can handle both text and images, needs a large context window, or is used for chat applications or code generation. Not as specialized for pure text-based NLP tasks compared to Text Bison.

## Tuning Parameters
  * `max_output_tokens`
  * `top_k` : sample from the k most likely next tokens at each step. Lower k focuses on higher probability tokens. Lower top-k also concentrates sampling on the highest probability tokens for each step. Recommended to set this value between 5 and 20. Sometimes, set it to 0 and adjust only `top_p` value.
  * `top_p` : the cumulative probability cutoff for token selection. Lower values mean sampling from a smaller, more top-weighted nucleus. Lower top-p values reduce diversity and focus on more probable tokens.
  * `temperature` : controls randomness, higher values increase diversity

## BigQuery SQL

### GoogleSQL
  * [VECTOR_SEARCH](https://cloud.google.com/bigquery/docs/reference/standard-sql/search_functions#vector_search): this function lets you search embeddings to find semantically similar entities. The output contains multiple rows from the base table that satisfy the search criteria.
    * Tuning
      * `top_k` : the number of nearest neighbors to return. The default value is 10.
      * `fraction_lists_to_search` : the higher this value, the more lists are searched, which increases the likelihood of finding the nearest neighbors(a.k.a. *recall*). However, the performance is slower relatively. The range is from `0.0` to `1.0`.
    * OUTPUT
      * `base`: A STRUCT value that contains all columns from base_table or a subset of the columns from base_table that you selected in the base_table_query_statement query.
      * `query`: A STRUCT value that contains all selected columns from the query data.
      * `distance`: A FLOAT64 value that represents the distance between the base data and the query data.  
  
### BigQuery ML SQL
  * [ML.GENERATE_EMBEDDING](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-embedding) : this function lets you create embeddings that describe an entity—for example, a piece of text or an image.
    * Model 
      * `multimodalembedding`
      * `text-embedding` : `ML.GENERATE_TEXT_EMBEDDING`을 대체
      * `text-multilingual-embedding`
      * PCA (Principal Component Analysis)
      * Autoencoder
      * Matrix Factorization

### INFORMATION SCHEMA view

**view the schema of a table**
```sql
select column_name, data_type from `[PROJECT_ID.]DATASET_ID.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'MY_TABLE';
```

# Competition List
1. Text Analysis of Media Industry Report
2. Analysis of Crime in Seoul
3. Analysis of Bike Rental System  in Seoul
4. Analysis of Speed Dating System (Kaggle)
5. Analysis of Indian Liver Patient(Kaggle)
