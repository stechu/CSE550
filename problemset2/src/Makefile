#####################################################################3
# CSE 550 Autumn 2014
#
# Problem Set 2
# Author: Vincent Lee
#
# Tests are separated to isolate any nasty hangovers between tests
# See design document for test case descriptions
#####################################################################3


all:
	run

test: client-test proposer-test acceptor-test integration-test

# automated client test
client-test:
	$(MAKE) clean && python -m unittest client_test.client_test.test_client_connection_loopback

# automated proposer tests
proposer-test:
	$(MAKE) clean && python -m unittest proposer_test.proposer_test.test_bring_up
	$(MAKE) clean && python -m unittest proposer_test.proposer_test.test_paxos_round
	$(MAKE) clean && python -m unittest proposer_test.proposer_test.test_proposal_timeouts
	$(MAKE) clean && python -m unittest proposer_test.proposer_test.test_instance_advancement

# automated acceptor tests
acceptor-test:
	$(MAKE) clean && python -m unittest acceptor_test.acceptor_test.test_bring_up
	$(MAKE) clean && python -m unittest acceptor_test.acceptor_test.test_single_proposal_prepare
	$(MAKE) clean && python -m unittest acceptor_test.acceptor_test.test_multiple_proposal_prepare
	$(MAKE) clean && python -m unittest acceptor_test.acceptor_test.test_multiple_instance_prepare
	$(MAKE) clean && python -m unittest acceptor_test.acceptor_test.test_multiple_prepare_accept
	$(MAKE) clean && python -m unittest acceptor_test.acceptor_test.test_reject_accept
	$(MAKE) clean && python -m unittest acceptor_test.acceptor_test.test_return_prepare_nack

# automated integration tests - manual verification
integration-test:
	$(MAKE) clean && python -m unittest integration_test.integration_test.test_bring_up
	$(MAKE) clean && python -m unittest integration_test.integration_test.test_single_client
	$(MAKE) clean && python -m unittest integration_test.integration_test.test_multi_client
	$(MAKE) clean && python -m unittest integration_test.integration_test.test_multi_server

# this test is manual verification and clean up
single-failure:
	$(MAKE) clean && python -m unittest failure_test.failure_test.test_single_server_failure

# this test is manual verification and clean up
multiple-failure:
	$(MAKE) clean && python -m unittest failure_test.failure_test.test_multi_server_failure

# automated message loss and duplication tests
message-test:
	$(MAKE) clean && python -m unittest msg_failure_test.msg_failure_test.test_message_drops
	$(MAKE) clean && python -m unittest msg_failure_test.msg_failure_test.test_message_duplication

run: 
	echo "TODO"
clean:
	rm -f *~ \#* *.o *.txt