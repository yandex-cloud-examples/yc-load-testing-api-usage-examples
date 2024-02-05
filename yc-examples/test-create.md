# Test creation

In the snippets, it is assumed that folder-id setting is already set in `yc`:

```bash
yc config set folder-id 'my_folder_id'
```

### 1. Prepare a set of agent

Here we assume that you already have a set of suitable LT agents.

```bash
export AGENT_ID='agent id'
```

On how to create an agent, see following guides:
- [How to create an agent in YC Compute](https://cloud.yandex.ru/en/docs/load-testing/operations/create-agent).
- [How to create an external agent](https://cloud.yandex.ru/en/docs/load-testing/tutorials/loadtesting-external-agent).

### 2. Prepare test yaml config

Upload your test configuration defined in YAML file.

```bash
export TEST_CONFIG_FILE="sample/_config_requests_in_file.yaml"

export TEST_CONFIG_ID=$(yc loadtesting test-config create --from-yaml-file $TEST_CONFIG_FILE --format json | jq -r ".id")
```

For information about config files, see [related documentation](https://yandextank.readthedocs.io/en/latest/config_reference.html#).

### 3. Prepare test payload

Upload test data payload.

```bash
export TEST_PAYLOAD_FILE_IN_CONFIG="requests.uri"
export TEST_PAYLOAD_FILE="sample/_requests.uri"
export S3_PAYLOAD_BUCKET="my_bucket"
export S3_PAYLOAD_FILENAME="my_requests.uri"

export YC_TOKEN=$(yc iam create-token)
curl -H "X-YaCloud-SubjectToken: $YC_TOKEN" --upload-file - "https://storage.yandexcloud.net/$S3_PAYLOAD_BUCKET/$S3_PAYLOAD_FILENAME" < $TEST_PAYLOAD_FILE
```

For information about data payload files, see [related documentation](https://cloud.yandex.ru/en/docs/load-testing/concepts/payload).

### 4. Start test

Given that all previous steps are done, start test with following command:

```bash

yc loadtesting test create \
    --name "yc-examples-test" \
    --description "Test has been created using YC" \
    --labels source=gh,type=tutorial \
    --configuration id=$TEST_CONFIG_ID,agent-id=$AGENT_ID,test-data=$TEST_PAYLOAD_FILE_IN_CONFIG \
    --test-data name=$TEST_PAYLOAD_FILE_IN_CONFIG,s3bucket=$S3_PAYLOAD_BUCKET,s3file=$S3_PAYLOAD_FILENAME

```

### 4.1 Start a multitest

You can also start a multitest using YC. A multitest is a test that utilizes multiple agents simulteneously,
thus surpassing a limit for a single load generation agent (either a bandwidth, cpu, or other resources).

```bash
export AGENT_ID1='first agent id'
export AGENT_ID2='second agent id'

yc loadtesting test create \
    --name "yc-examples-test" \
    --description "Test has been created using YC" \
    --labels source=gh,type=tutorial,kind=multi \
    --configuration id=$TEST_CONFIG_ID,agent-id=$AGENT_ID1,test-data=$TEST_PAYLOAD_FILE_IN_CONFIG \
    --configuration id=$TEST_CONFIG_ID,agent-id=$AGENT_ID2,test-data=$TEST_PAYLOAD_FILE_IN_CONFIG \
    --test-data name=$TEST_PAYLOAD_FILE_IN_CONFIG,s3bucket=$S3_PAYLOAD_BUCKET,s3file=$S3_PAYLOAD_FILENAME
```
