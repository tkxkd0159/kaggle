https://console.cloud.google.com/bigquery

# Parameters
* Dataset : `lgcns-gkh-p28.ds_gkh_p28`
  * It provides a dataset that chunk a given PDF data to a certain size. Each chunked text is not more than 100/300/500/700/1000 characters.
  * TB_PDF_C100, TB_PDF_C300, TB_PDF_C500, TB_PDF_C700, TB_PDF_C1000
* Model
  * `embeddingmodel` : a model to generate text embeddings for tasks like semantic search, information retrieval, or recommendation systems. Not designed for general text generation or understanding tasks
  * clustering model : `cluster_c<chunk-size>_n<n-of-cluster>`
  * `txtbison` (PaLM 2) : a model for a variety of text-based NLP tasks and prioritize language understanding/generation.
  * `gemini-pro10`, `gemini-pro15` : model that can handle both text and images, needs a large context window, or is used for chat applications or code generation. Not as specialized for pure text-based NLP tasks compared to Text Bison.
* Tuning Parameters
  * `max_output_tokens`
  * `top_k`
  * `top_p`
  * `temperature` : controls randomness, higher values increase diversity
  * `fraction_lists_to_search` : specifies the percentage of lists to search (0.0 ~ 1.0)

# BigQuery SQL
* `GoogleSQL`
  * `VECTOR_SEARCH`: this function lets you search embeddings to find semantically similar entities. The output contains multiple rows from the base table that satisfy the search criteria.
* BigQuery ML SQL
  * `ML.GENERATE_EMBEDDING` : this function lets you create embeddings that describe an entity—for example, a piece of text or an image.

---
- [Set up](#set-up)
  - [create a remote AI model in BigQuery](#create-a-remote-ai-model-in-bigquery)
  - [Generate embedding tables from chunked text (100, 300, 500, 700, 1000)](#generate-embedding-tables-from-chunked-text-100-300-500-700-1000)
  - [Generate K-means clustering model (only for K-means clustering prediction)](#generate-k-means-clustering-model-only-for-k-means-clustering-prediction)
  - [Make procedures for prediction](#make-procedures-for-prediction)
    - [K-means Clustering](#k-means-clustering)
    - [Vecter Search](#vecter-search)
  - [Predict answers using models](#predict-answers-using-models)
  - [Check Data](#check-data)
  - [Decision](#decision)

# Set up

## create a remote AI model in BigQuery
```sql
-- Create embedding model
CREATE OR REPLACE MODEL `lgcns-gkh-p28.ds_gkh_p28.embeddingmodel`
REMOTE WITH CONNECTION `us.vtx-multi-gkh-p28`
OPTIONS (ENDPOINT = 'textembedding-gecko-multilingual');

-- Create PaLM2 text bison model
CREATE OR REPLACE MODEL `lgcns-gkh-p28.ds_gkh_p28.txtbison`
REMOTE WITH CONNECTION `us.vtx-multi-gkh-p28`
OPTIONS (ENDPOINT = 'text-bison');

-- Create Gemini 1.0 pro
CREATE OR REPLACE MODEL `lgcns-gkh-p28.ds_gkh_p28.gemini-pro10`
REMOTE WITH CONNECTION `us.vtx-multi-gkh-p28`
OPTIONS (ENDPOINT = 'gemini-1.0-pro');

-- Create Gemini 1.5 pro
CREATE OR REPLACE MODEL `lgcns-gkh-p28.ds_gkh_p28.gemini-pro15`
REMOTE WITH CONNECTION `us.vtx-multi-gkh-p28`
OPTIONS (ENDPOINT = 'gemini-1.5-pro');
```

## Generate embedding tables from chunked text (100, 300, 500, 700, 1000)
```sql
CREATE TABLE `lgcns-gkh-p28.ds_gkh_p28.TB_VECTOR_C100`
AS
(
SELECT *
FROM
  ML.GENERATE_TEXT_EMBEDDING
  (
    MODEL `lgcns-gkh-p28.ds_gkh_p28.embeddingmodel`,
    (
     SELECT 
       chunks AS content
     FROM 
       `lgcns-gkh-p28.ds_gkh_p28.TB_PDF_C100`
    ),
    STRUCT(TRUE AS flatten_json_output)
  )
);
```

## Generate K-means clustering model (only for K-means clustering prediction)
```sql
CREATE OR REPLACE MODEL `lgcns-gkh-p28.ds_gkh_p28.cluster_c###_n#`
OPTIONS (
  model_type = 'KMEANS',
  KMEANS_INIT_METHOD = 'KMEANS++',
  num_clusters = 4) AS (   -- n-of-cluster
    SELECT
      text_embedding
    FROM
      `lgcns-gkh-p28.ds_gkh_p28.TB_VECTOR_C###` -- enter the embedding table name to be used when creating a K-means model. (e.g. TB_VECTOR_C###)
);
```


## Make procedures for prediction
### K-means Clustering
```sql
BEGIN
  DECLARE answer STRING;
  DECLARE reference STRING;
  DECLARE prompt_pre STRING DEFAULT '당신은 지금부터 주식시장의 전문가이면서 특히 엔터테인먼트 및 방송연애관련 전문가입니다.사용자의 질문과 그에 대한 참고 데이터가 아래에 있고, 이를 참고해서 답변해주세요';
  SET reference = (
  WITH query_test AS
      (
        SELECT
          *
        FROM
          ML.GENERATE_TEXT_EMBEDDING(
            MODEL `lgcns-gkh-p28.ds_gkh_p28.embeddingmodel`,
            (SELECT
              question AS content),
              STRUCT(TRUE AS flatten_json_output))
      ),
      query_cluster AS
      (
        SELECT
          centroid_id,
          content,
          text_embedding
        FROM
          ML.PREDICT(
            MODEL `lgcns-gkh-p28.ds_gkh_p28.cluster_c500_n5`, # 클러스터를 변경해서 성능비교를 해주세요
            (SELECT
               text_embedding,
               content
             FROM
               query_test)
          )
        ),
      answer_cluster AS
      (
        SELECT
          *
        FROM
          ML.PREDICT(
            MODEL `lgcns-gkh-p28.ds_gkh_p28.cluster_c500_n5`, # 클러스터를 변경해서 성능비교를 해주세요
            (SELECT
               text_embedding,
               content
             FROM
               `lgcns-gkh-p28.ds_gkh_p28.TB_VECTOR_C500`) # 벡터 테이블을 변경해서 성능비교를 해주세요
          )
        WHERE centroid_id IN (SELECT centroid_id FROM query_cluster)
      ),
      datapoint AS 
      (
        SELECT
        s.content AS search_content,
        c.content AS content,
        ML.DISTANCE(s.text_embedding, c.text_embedding, 'COSINE') AS distance
        FROM
        query_cluster AS s,
        answer_cluster AS c
        ORDER BY
        distance ASC LIMIT 10 # 상위 몇개의 결과까지 참고데이터로 사용할지 숫자를 넣어주세요
          )
      SELECT STRING_AGG(content, '\n\n') AS con FROM datapoint
      );
  SET answer = (
      SELECT 
        STRING(ml_generate_text_result['candidates'][0]['content']['parts'][0]['text']) AS answer 
      FROM
        ML.GENERATE_TEXT(
          MODEL `lgcns-gkh-p28.ds_gkh_p28.gemini-pro15`,
          (
            SELECT
              CONCAT(
                prompt_pre,
                '질문：',question,
                '참고 데이터：', reference
                ) AS prompt
          ),
          STRUCT(
            0.1 AS temperature,
            1000 AS max_output_tokens,
            0.8 AS top_p,
            10 AS top_k))
  );
  SET result = (
    SELECT TO_JSON_STRING(STRUCT(question, answer, reference))
  );
END
```

### Vecter Search (Pick)
```sql
CREATE OR REPLACE PROCEDURE `lgcns-gkh-p28.ds_gkh_p28.vsg_c1000`(question STRING, OUT result STRING)
BEGIN
  DECLARE answer STRING;
  DECLARE reference STRING;
  DECLARE prompt_pre STRING DEFAULT '지금부터 주식시장의 전문가이면서 특히 엔터테인먼트 및 방송연애관련 전문가입니다. 참고데이터를 기준으로 답변을 작성해주세요.';
  SET reference =(
    SELECT STRING_AGG(base.content, '\n\n') AS combined_content
    FROM VECTOR_SEARCH (
    TABLE `lgcns-gkh-p28.ds_gkh_p28.TB_VECTOR_C1000`, 'text_embedding', -- use `text_embedding` column to search for nearest neighbor embeddings
    ( -- A query that provides the embeddings for which to find nearest neighbors. All columns are passed through as output columns.
     SELECT ml_generate_embedding_result, content AS query
     FROM ML.GENERATE_EMBEDDING(
     MODEL `lgcns-gkh-p28.ds_gkh_p28.embeddingmodel`,
    (SELECT question AS content)
    )
  ),
  top_k => 5, options => '{"fraction_lists_to_search": 0.01}')
 );
  SET answer = (
      SELECT 
        STRING(ml_generate_text_result['candidates'][0]['content']['parts'][0]['text']) AS answer
      FROM
        ML.GENERATE_TEXT(
          MODEL `lgcns-gkh-p28.ds_gkh_p28.gemini-pro15`,
          (
            SELECT
              CONCAT(
                prompt_pre,
                '질문：',question,
                '참고 데이터：',reference
                ) AS prompt
          ),
          STRUCT(
            0.1 AS temperature,
            1000 AS max_output_tokens,
            0.8 AS top_p,
            10 AS top_k)) -- recommend from 5 to 20
  );
  SET result = (
    SELECT TO_JSON_STRING(STRUCT(question, answer, reference))
  );
END;
```

## Predict answers using models
```sql
DECLARE i INT64 DEFAULT 1;
DECLARE result STRING;

CREATE OR REPLACE TABLE `lgcns-gkh-p28.ds_gkh_p28.TB_SUBMIT02` (
    Id INT64,
    question STRING,
    Predicted STRING,
    reference STRING,
);

FOR item IN (
  SELECT question AS Q 
  FROM `lgcns-gkh-p28.ds_gkh_p28.TB_QUESTION`)
DO
  CALL `lgcns-gkh-p28.ds_gkh_p28.vsg_c500` (item.Q, result);
  INSERT INTO `lgcns-gkh-p28.ds_gkh_p28.TB_SUBMIT02`
  SELECT
  i,
  JSON_EXTRACT_SCALAR(result, '$.question') AS question,
  JSON_EXTRACT_SCALAR(result, '$.answer') AS answer,
  JSON_EXTRACT_SCALAR(result, '$.reference') AS reference;
  SET i = i + 1;
END FOR;
```

## Check Data
```sql
-- Check keywords and predicted text
SELECT 
  c.id,
  c.keyword,
  s.Predicted
FROM 
  `lgcns-gkh-p28.ds_gkh_p28.TB_SUBMIT##` s
JOIN 
  `lgcns-gkh-p28.ds_gkh_p28.TB_KEYWORD` c
ON 
  s.id = c.id
ORDER BY c.id;

-- Submision - converting the predicted text to embeddings
SELECT
  ROW_NUMBER() OVER () AS Id, 
  text_embedding AS Predicted
FROM
  ML.GENERATE_TEXT_EMBEDDING(
    MODEL `lgcns-gkh-p28.ds_gkh_p28.embeddingmodel`,
      (SELECT Predicted AS content FROM `lgcns-gkh-p28.ds_gkh_p28.TB_SUBMIT##` ORDER BY Id),
      STRUCT(TRUE AS flatten_json_output)
      ); 
```

## Decision
I will pick Vector Search for the final model.
**Why Vector Search is Better:**
* Keyword Focus: Vector search is designed to handle keyword-based queries effectively. It can measure the semantic similarity between the question's keywords and the content in the report, leading to more accurate and relevant answers.
* Contextual Understanding: Vector search considers the context of words and phrases, not just their exact match. This means it can find relevant passages even if they use synonyms or slightly different wording than the question's keywords.
* Flexibility: Vector search can be easily adapted to handle variations in query style and language. It can even accommodate fuzzy matching, allowing for some degree of misspellings or word variations.
* Evaluation: Your requirement of highly evaluating answers with specific keywords aligns perfectly with the strengths of vector search. It can directly measure the presence and importance of keywords in the identified answers.