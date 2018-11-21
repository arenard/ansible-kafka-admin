"""
Main tests for library
"""

import os
import six

import testinfra.utils.ansible_runner
from tests.utils import KafkaManager


testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts(['kafka1*', 'kafka2*'])
localhost = testinfra.get_host(
    'localhost',
    connection='ansible',
    ansible_inventory=os.environ['MOLECULE_INVENTORY_FILE']
)
localhost_vars = localhost.ansible.get_variables()


def test_configured_topic(host):
    """
    Test if topic configuration is what was defined
    """
    ansible_vars = host.ansible.get_variables()
    topic_configuration = localhost_vars['topic_defaut_configuration']
    topic_name = localhost_vars['topic_name']
    kafka_servers = ansible_vars['ansible_eth0']['ipv4']['address']+':9092'

    # Forcing api_version to 0.11.0 in order to be sure that a
    # Metadata_v1 is sent (so that we get the controller info)
    kafka_client = KafkaManager(
        bootstrap_servers=kafka_servers,
        api_version=(0, 11, 0)
    )

    if topic_configuration['state'] == 'present':
        assert topic_name in kafka_client.get_topics()

        partitions = kafka_client.get_total_partitions_for_topic(topic_name)
        assert partitions == topic_configuration['partitions']

        ite = kafka_client.get_partitions_metadata_for_topic(topic_name)
        for _, metadata in six.iteritems(ite):
            tot_replica = len(metadata.replicas)
            assert tot_replica == topic_configuration['replica_factor']

        for key, value in topic_configuration['options'].iteritems():
            config = kafka_client.get_config_for_topic(topic_name, key)
            assert str(config) == str(value)
    else:
        assert topic_name not in kafka_client.get_topics()

    kafka_client.close()
