######################################################
# Makefile for project
######################################################

KEY_NAME=team_404_error
KEY_FILE=keys/key.pem
REGION=us-west-2
SLAVE_NODES=16
CLUSTER_NAME=ECHO_BASE_2

all:
	echo TODO

# bring up the cluster
launch:
	spark-ec2 -k $(KEY_NAME) -i $(shell pwd)/$(KEY_FILE) -s $(SLAVE_NODES) --region $(REGION) launch $(CLUSTER_NAME)

# connect to the cluster
login:
	spark-ec2 -k $(KEY_NAME) -i $(shell pwd)/$(KEY_FILE) -s $(SLAVE_NODES) --region $(REGION) login $(CLUSTER_NAME)

# stop the cluster
stop:
	spark-ec2 stop $(CLUSTER_NAME) --region $(REGION)

# resume the cluster
resume:
	spark-ec2 -i $(shell pwd)/$(KEY_FILE) start $(CLUSTER_NAME) --region $(REGION)

# terminate the cluster
destroy:
	spark-ec2 destroy $(CLUSTER_NAME) --region $(REGION)