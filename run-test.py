import requests
import json
import grpc
import time
import uuid 
from zeebe_grpc import gateway_pb2, gateway_pb2_grpc
from confluent_kafka import Consumer, KafkaError
from elasticsearch import Elasticsearch

def startWorkflowInstances(numberOfInstances):
	file = open('payloads/payload1.json', 'r')
	payload = file.read()
	with grpc.insecure_channel("localhost:26500") as channel:
		stub = gateway_pb2_grpc.GatewayStub(channel)
		for i in range(0, numberOfInstances):
			stub.CreateWorkflowInstance(gateway_pb2.CreateWorkflowInstanceRequest(
				bpmnProcessId = 'ping-pong', 
				version = -1, 
				variables = payload..replace('RANDOM', uuid.uuid1())))	

def startKafkaConnectSource():
	contents = open('source.json', 'rb').read()
	headers = {'Content-type': 'application/json'}
	response = requests.post('http://localhost:8083/connectors', data=contents, headers=headers)
	print "Kafka Connect response: " + str( response )

def deleteKafkaConnectSource():
	print "todo"

def startKafkaConnectSink():
	contents = open('sink.json', 'rb').read()
	headers = {'Content-type': 'application/json'}
	response = requests.post('http://localhost:8083/connectors', data=contents, headers=headers)
	print "Kafka Connect response: " + str( response )

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

def waitForWorkflowsToBeFinished(numberOfEpectedMessages):
	es = Elasticsearch()
	res = es.count(
		index="zeebe-record-workflow-instance")
	print("Got " + str(res['count']))


number = 10

print( "## Start Workflow Instances" )
start = time.clock()
startWorkflowInstances(number)
end = time.clock()
print( "Started "+str(number)+" workflow instances: " + str((end - start) * 10000) + ' milliseconds' );

print( "## Start Kafka Connect Source" )
start = time.clock()
startKafkaConnectSource()
end = time.clock()
print( "Started Source: " + str((end - start) * 10000) + ' milliseconds' );

print( "## Start Kafka Consumer to Check for Messages" )
start = time.clock()
waitForRecordsToArrive(number)
end = time.clock()
print( str(number) + " records arrived on topic 'pong' in Kafka: " + str((end - start) * 10000) + ' milliseconds' );

print( "## Start Kafka Connect Source" )
start = time.clock()
startKafkaConnectSink()
end = time.clock()
print( "Started Sink: " + str((end - start) * 10000) + ' milliseconds' );

waitForWorkflowsToBeFinished(number)
