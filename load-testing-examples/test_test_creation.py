import uuid

import pytest
import yandexcloud
from common import (
    DEFAULT_AGENT_NAME_PREFIX,
    ENV_VARS,
    generate_create_agent_request,
    wait_for_agent_to_be_ready,
    wait_for_condition,
)
from grpc import StatusCode
from grpc._channel import _InactiveRpcError
from yandex.cloud.loadtesting.api.v1.agent.agent_pb2 import Agent
from yandex.cloud.loadtesting.api.v1.agent_service_pb2 import (
    CreateAgentMetadata,
    DeleteAgentRequest,
    GetAgentRequest,
)
from yandex.cloud.loadtesting.api.v1.agent_service_pb2_grpc import AgentServiceStub
from yandex.cloud.loadtesting.api.v1.config.config_pb2 import Config
from yandex.cloud.loadtesting.api.v1.config_service_pb2 import (
    CreateConfigMetadata,
    CreateConfigRequest,
)
from yandex.cloud.loadtesting.api.v1.config_service_pb2_grpc import ConfigServiceStub
from yandex.cloud.loadtesting.api.v1.report_service_pb2 import (
    GetTableReportRequest,
    GetTableReportResponse,
)
from yandex.cloud.loadtesting.api.v1.report_service_pb2_grpc import ReportServiceStub
from yandex.cloud.loadtesting.api.v1.test.agent_selector_pb2 import AgentSelector
from yandex.cloud.loadtesting.api.v1.test.details_pb2 import Details
from yandex.cloud.loadtesting.api.v1.test.single_agent_configuration_pb2 import (
    SingleAgentConfiguration,
)
from yandex.cloud.loadtesting.api.v1.test.test_pb2 import Test
from yandex.cloud.loadtesting.api.v1.test.status_pb2 import Status
from yandex.cloud.loadtesting.api.v1.test_service_pb2 import (
    CreateTestMetadata,
    CreateTestRequest,
    GetTestRequest,
    StopTestRequest,
    DeleteTestRequest,
    ListTestsRequest,
)
from yandex.cloud.loadtesting.api.v1.test_service_pb2_grpc import TestServiceStub

TEST_CONFIG_TEMPLATE = """
uploader:
  enabled: true
  package: yandextank.plugins.DataUploader
  job_name: pytest-examlple
  job_dsc: ''
  ver: ''
  api_address: loadtesting.api.cloud.yandex.net:443
phantom:
  enabled: true
  package: yandextank.plugins.Phantom
  address: {target_ip}:80
  ammo_type: uri
  load_profile:
    load_type: rps
    schedule: line(1,100,20s)
  ssl: false
  instances: 1000
  uris:
    - /index
    - /static
"""


@pytest.fixture
def create_agent_for_test(sdk: yandexcloud.SDK):
    agent_service = sdk.client(AgentServiceStub)

    name = f'{DEFAULT_AGENT_NAME_PREFIX}{uuid.uuid4().hex[:5]}'
    request = generate_create_agent_request(name)
    agent_create_operation = agent_service.Create(request)
    agent = sdk.wait_operation_and_get_result(
        agent_create_operation,
        response_type=Agent,
        meta_type=CreateAgentMetadata,
        timeout=20 * 60,
    ).response

    wait_for_agent_to_be_ready(agent_service, agent.id)
    try:
        yield agent
    finally:
        delete_operation = agent_service.Delete(DeleteAgentRequest(agent_id=agent.id))
        sdk.wait_operation_and_get_result(delete_operation)

        with pytest.raises(_InactiveRpcError) as err_info:
            agent_service.Get(GetAgentRequest(agent_id=agent.id))
        assert err_info.value.code() is StatusCode.NOT_FOUND


def test_test_creation(sdk: yandexcloud.SDK, create_agent_for_test):
    agent_id = create_agent_for_test.id
    config_stub: ConfigServiceStub = sdk.client(ConfigServiceStub)
    create_config_operation = config_stub.Create(
        CreateConfigRequest(
            folder_id=ENV_VARS.folder_id(),
            yaml_string=TEST_CONFIG_TEMPLATE.format(target_ip=ENV_VARS.target_IP()),
        )
    )
    config_id = sdk.wait_operation_and_get_result(
        create_config_operation,
        response_type=Config,
        meta_type=CreateConfigMetadata,
        timeout=60,
    ).response.id

    create_test_request = CreateTestRequest(
        folder_id=ENV_VARS.folder_id(),
        configurations=[
            SingleAgentConfiguration(
                config_id=config_id, agent_selector=AgentSelector(agent_id=agent_id)
            )
        ],
        test_details=Details(name='ete_created'),
    )

    test_stub: TestServiceStub = sdk.client(TestServiceStub)
    create_test_operation = test_stub.Create(create_test_request)
    test_id = sdk.wait_operation_and_get_result(
        create_test_operation,
        response_type=Test,
        meta_type=CreateTestMetadata,
        timeout=60,
    ).response.id

    get_test_request = GetTestRequest(test_id=test_id)
    wait_for_condition(
        'wait for test is finished',
        lambda: test_stub.Get(get_test_request).summary.is_finished,
        timeout=3 * 60,
        step=1,
    )

    report_stub: ReportServiceStub = sdk.client(ReportServiceStub)
    get_report_request = GetTableReportRequest(test_id=test_id)
    report: GetTableReportResponse = report_stub.GetTable(get_report_request)

    assert 200 in report.overall.http_codes


def test_test_interrupt(sdk: yandexcloud.SDK, create_agent_for_test):
    agent_id = create_agent_for_test.id
    config_stub: ConfigServiceStub = sdk.client(ConfigServiceStub)
    create_config_operation = config_stub.Create(
        CreateConfigRequest(
            folder_id=ENV_VARS.folder_id(),
            yaml_string=TEST_CONFIG_TEMPLATE.format(target_ip=ENV_VARS.target_IP()),
        )
    )
    config_id = sdk.wait_operation_and_get_result(
        create_config_operation,
        response_type=Config,
        meta_type=CreateConfigMetadata,
        timeout=60,
    ).response.id

    create_test_request = CreateTestRequest(
        folder_id=ENV_VARS.folder_id(),
        configurations=[
            SingleAgentConfiguration(
                config_id=config_id, agent_selector=AgentSelector(agent_id=agent_id)
            )
        ],
        test_details=Details(name='ete_created'),
    )

    test_stub: TestServiceStub = sdk.client(TestServiceStub)
    create_test_operation = test_stub.Create(create_test_request)
    test_id = sdk.wait_operation_and_get_result(
        create_test_operation,
        response_type=Test,
        meta_type=CreateTestMetadata,
        timeout=60,
    ).response.id

    # wait until test is started
    get_test_request = GetTestRequest(test_id=test_id)
    wait_for_condition(
        'wait for test execution start',
        lambda: test_stub.Get(get_test_request).summary.status != Status.CREATED,
        timeout=3 * 60,
        step=1,
    )

    # stop the test
    stop_test_operation = test_stub.Stop(StopTestRequest(test_id=test_id))
    test: Test = sdk.wait_operation_and_get_result(
        stop_test_operation,
        response_type=Test,
        timeout=3 * 60,
    ).response

    assert test.summary.is_finished

    # delete the test
    delete_test_operation = test_stub.Delete(DeleteTestRequest(test_id=test_id))
    sdk.wait_operation_and_get_result(
        delete_test_operation,
        timeout=3 * 60,
    )

    # confirm the test is deleted
    list_tests_res = test_stub.List(
        ListTestsRequest(folder_id=ENV_VARS.folder_id(), filter=f'id = {test_id}')
    )
    assert len(list_tests_res.tests) == 0
