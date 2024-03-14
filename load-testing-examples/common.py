import os
import time
import typing

from yandex.cloud.loadtesting.api.v1.agent.agent_pb2 import Agent
from yandex.cloud.loadtesting.api.v1.agent.create_compute_instance_pb2 import \
    CreateComputeInstance
from yandex.cloud.loadtesting.api.v1.agent.status_pb2 import Status
from yandex.cloud.loadtesting.api.v1.agent_service_pb2 import (
    CreateAgentRequest, GetAgentRequest)


DEFAULT_AGENT_NAME_PREFIX = 'ete-'
class ENV_VARS:
    @staticmethod
    def token():
        return os.environ['YC_TOKEN']
    @staticmethod
    def folder_id():
        return os.environ['FOLDER_ID']
    @staticmethod
    def service_account_id():
        return os.environ['SERVICE_ACCOUNT_ID']
    @staticmethod
    def subnet_id():
        return os.environ['SUBNET_ID']
    @staticmethod
    def security_group_id():
        return os.environ['SECURITY_GROUP_ID']
    @staticmethod
    def agent_ssh_keys():
        return os.environ['AGENT_SSH_KEYS']
    @staticmethod
    def target_IP():
        return os.environ['TARGET_IP']


def generate_create_agent_request(name):
    return CreateAgentRequest(
        folder_id=ENV_VARS.folder_id(),
        name=name,
        compute_instance_params=CreateComputeInstance(
            zone_id='ru-central1-b',
            service_account_id=ENV_VARS.service_account_id(),
            resources_spec={
                'memory': 2147483648,
                'cores': 2,
            },
            boot_disk_spec={
                'disk_spec': {'size': 16106127360},
                'auto_delete': True,
            },
            network_interface_specs=[
                {
                    'subnet_id': ENV_VARS.subnet_id(),
                    'primary_v4_address_spec': {},
                    'security_group_ids': (
                        [ENV_VARS.security_group_id()]
                        if ENV_VARS.security_group_id()
                        else []
                    ),
                },
            ],
            metadata={'ssh-keys': ENV_VARS.agent_ssh_keys()},
        ),
    )

def wait_for_agent_to_be_ready(agent_stub, agent_id, timeout=15 * 60):
    request = GetAgentRequest(agent_id=agent_id)
    wait_for_condition(
        'wait for agent to be ready',
        lambda: agent_stub.Get(request).status == Status.READY_FOR_TEST,
        timeout=timeout,
        step=10,
    )


def wait_for_condition(
    op_name: str,
    condition: typing.Callable[[], bool],
    timeout: int,
    step: int,
):
    for seconds in range(1, timeout, step):
        if condition():
            return
        time.sleep(step)
    else:
        raise Exception(f'[{op_name or "operation"}] timeout: waited {seconds=}')
