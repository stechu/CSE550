######################################################
# Makefile for project
######################################################

KEY_NAME=team_404_error
KEY_FILE=keys/key.pem
REGION=us-west-2
SLAVE_NODES=1
CLUSTER_NAME=ECHO_BASE

all:
	echo TODO

# bring up the cluster
setup:
	spark-ec2 -k $(KEY_NAME) -i $(KEY_FILE) -s $(SLAVE_NODES) --region $(REGION) launch $(ECHO_BASE)

terminate:
	spark-ec2 destroy $(CLUSTER_NAME)