https://console.cloud.google.com/bigquery

# Parameters
* Dataset : `lgcns-gkh-p28.ds_gkh_p28`
  * It provides a dataset that chunk a given PDF data to a certain size. Each chunked text is not more than 100/300/500/700/1000 characters.
  * TB_PDF_C100, TB_PDF_C300, TB_PDF_C500, TB_PDF_C700, TB_PDF_C1000

---

- [Set up](#set-up)
  - [create a remote AI model in BigQuery](#create-a-remote-ai-model-in-bigquery)
  - [Generate embedding tables from chunked text (100, 300, 500, 700, 1000)](#generate-embedding-tables-from-chunked-text-100-300-500-700-1000)
  - [Generate K-means clustering model (only for K-means clustering prediction)](#generate-k-means-clustering-model-only-for-k-means-clustering-prediction)
  - [Make procedures for prediction](#make-procedures-for-prediction)
    - [Vecter Search](#vecter-search)
  - [Predict answers using models](#predict-answers-using-models)
    - [K-means Clustering](#k-means-clustering)
  - [Check Data](#check-data)
  - [Decision](#decision)

# Set up

## create a remote AI model in BigQuery
```sql
-- Create an embedding model
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

### Vecter Search
1. Generate a vector embedding from question input and use it as `query`.
2. Use `VECTOR_SEARCH` function to search for nearest neighbor embeddings for embedded question input `text_embedding` column.
3. Use the result of the `VECTOR_SEARCH` function as a *reference* for the `ML.GENERATE_TEXT` function.
4. Use the `ML.GENERATE_TEXT` function to generate the answer based on the *reference* and the question input.
```sql
CREATE OR REPLACE PROCEDURE `lgcns-gkh-p28.ds_gkh_p28.vsg_c1000`(question STRING, OUT result STRING)
BEGIN
  DECLARE answer STRING;
  DECLARE reference STRING;
  DECLARE prompt_pre STRING DEFAULT '당신은 지금부터 주식시장의 전문가이면서 특히 엔터테인먼트 및 방송연애관련 전문가입니다. 사용자의 질문과 그에 대한 참고 데이터가 아래에 있고, 이를 참고해서 답변해주세요';
  SET reference =(
    SELECT STRING_AGG(base.content, '\n\n') AS combined_content
    FROM VECTOR_SEARCH (
    TABLE `lgcns-gkh-p28.ds_gkh_p28.TB_VECTOR_C1000`, 'text_embedding',
    (
     SELECT ml_generate_embedding_result, content
     FROM ML.GENERATE_EMBEDDING(
     MODEL `lgcns-gkh-p28.ds_gkh_p28.embeddingmodel`,
    (SELECT question AS content)
    )
  ),
  top_k => 20, options => '{"fraction_lists_to_search": 0.01}')
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
            10 AS top_k))
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

### K-means Clustering
```sql
BEGIN
  DECLARE answer STRING;
  DECLARE reference STRING;
  DECLARE prompt_pre STRING DEFAULT '당신은 지금부터 주식시장의 전문가이면서 특히 엔터테인먼트 및 방송연애관련 전문가입니다. 사용자의 질문과 그에 대한 참고 데이터가 아래에 있고, 이를 참고해서 답변해주세요';
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
            MODEL `lgcns-gkh-p28.ds_gkh_p28.cluster_c500_n5`,
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
            MODEL `lgcns-gkh-p28.ds_gkh_p28.cluster_c500_n5`,
            (SELECT
               text_embedding,
               content
             FROM
               `lgcns-gkh-p28.ds_gkh_p28.TB_VECTOR_C500`)
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
        distance ASC LIMIT 10 -- set how many of the results you want to refer
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