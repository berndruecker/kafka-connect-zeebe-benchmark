import requests
import json
import grpc
import time
import uuid 
import sys
from timeit import default_timer as timer
from datetime import timedelta
from zeebe_grpc import gateway_pb2, gateway_pb2_grpc
from confluent_kafka import Consumer, KafkaError
from prometheus_client.parser import text_string_to_metric_families


def startWorkflowInstances(numberOfInstances, payload):
	file = open('payloads/payload-'+payload+'.json', 'r')
	payload = file.read()
	with grpc.insecure_channel("localhost:26500") as channel:
		stub = gateway_pb2_grpc.GatewayStub(channel)
		for i in range(0, numberOfInstances):
			stub.CreateWorkflowInstance(gateway_pb2.CreateWorkflowInstanceRequest(
				bpmnProcessId = 'ping-pong', 
				version = -1, 
				variables = payload.replace('RANDOM', str(uuid.uuid1()))))

def startKafkaConnectSource():
	contents = open('source.json', 'rb').read()
	headers = {'Content-type': 'application/json'}
	response = requests.post('http://localhost:8083/connectors', data=contents, headers=headers)
	print "Kafka Connect response: " + str( response )

def deleteKafkaConnectSource():
	response = requests.delete('http://localhost:8083/connectors/ping')
	print "Kafka Connect delete response: " + str( response )

def startKafkaConnectSink():
	contents = open('sink.json', 'rb').read()
	headers = {'Content-type': 'application/json'}
	response = requests.post('http://localhost:8083/connectors', data=contents, headers=headers)
	print "Kafka Connect response: " + str( response )

def deleteKafkaConnectSink():
	response = requests.delete('http://localhost:8083/connectors/pong')
	print "Kafka Connect delete response: " + str( response )

def waitForRecordsToArrive(numberOfEpectedMessages):
	amount = 0
	settings = {
		'bootstrap.servers': 'localhost:9092',
		'group.id': 'mygroup',
		'client.id': 'client-1',
		'enable.auto.commit': True,
		'session.timeout.ms': 6000,
		'default.topic.config': {'auto.offset.reset': 'smallest'}
	}
	c = Consumer(settings)
	c.subscribe(['pong'])

	try:
		topicNotEmpty = True
		while (amount<numberOfEpectedMessages or topicNotEmpty):
			msg = c.poll(0.1)
			if msg is None:
				topicNotEmpty = False
				continue
			elif not msg.error():
				amount += 1
				topicNotEmpty = True

			elif msg.error().code() == KafkaError._PARTITION_EOF:
				print('End of partition reached {0}/{1}'
					  .format(msg.topic(), msg.partition()))
			else:
				print('Error occured: {0}'.format(msg.error().str()))

	except KeyboardInterrupt:
		pass

	finally:
		c.close()
		print("Received "+ str(amount) + " records on Kafka")

def getMetricValue(metricName):
	metrics = requests.get("http://localhost:9600/metrics").content
	for family in text_string_to_metric_families(metrics):
		for sample in family.samples:
			if (sample[0]==metricName):
				runningWorkflows = sample[2]
				return runningWorkflows


def waitForWorkflowsToBeFinished():
	numberOfWorkflowsRunning = 1;
	while (numberOfWorkflowsRunning > 0):
		numberOfWorkflowsRunning = getMetricValue("zeebe_running_workflow_instances_total");

def waitForJobsToBeFinished():
	numberOfJobsPending = 1;
	while (numberOfJobsPending > 0):
		numberOfJobsPending = getMetricValue("zeebe_pending_jobs_total");

if (len(sys.argv[0])==2):
	number = int(sys.argv[0])
	payload = str(sys.argv[1])
else:
	number = 1
	payload = "1"

print( "####### Starting with number of instances: " + str(number) + ", payload: " + payload)

print( "## Start Workflow Instances ")
start = timer()
startWorkflowInstances(number, payload)
print(timedelta(seconds=timer()-start))

print( "## Start Kafka Connect Source" )
startKafkaConnectSource()

print( "## Wait for all jobs in Zeebe to be processed" )
start = timer()
waitForJobsToBeFinished()
print(timedelta(seconds=timer()-start))

print( "## Start Kafka Consumer to Check for Messages" )
start = timer()
waitForRecordsToArrive(number)
print(timedelta(seconds=timer()-start))

print( "## Stop Kafka Connect Source" )
deleteKafkaConnectSource()

print( "## Start Kafka Connect Sink" )
startKafkaConnectSink()

print( "## Wait for workflows to be finished" )
start = timer()
waitForWorkflowsToBeFinished()
print(timedelta(seconds=timer()-start))

print( "## Stop Kafka Connect Sink" )
deleteKafkaConnectSink()
