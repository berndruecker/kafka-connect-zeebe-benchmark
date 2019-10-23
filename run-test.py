import requests
import json
import grpc
import time
from zeebe_grpc import gateway_pb2, gateway_pb2_grpc
from confluent_kafka import Consumer, KafkaError

def startWorkflowInstances(numberOfInstances):
	with grpc.insecure_channel("localhost:26500") as channel:
		stub = gateway_pb2_grpc.GatewayStub(channel)
		for i in range(0, numberOfInstances):
			stub.CreateWorkflowInstance(gateway_pb2.CreateWorkflowInstanceRequest(
			bpmnProcessId = 'ping-pong', version = -1, variables = '{"orderId" : "ab1234"}'))	

def startKafkaConnectSource():
	contents = open('source.json', 'rb').read()
	headers = {'Content-type': 'application/json'}
	response = requests.post('http://localhost:8083/connectors', data=contents, headers=headers)
	print "Kafka Connect response: " + str( response )

def startKafkaConnectSink():
	contents = open('sink.json', 'rb').read()
	headers = {'Content-type': 'application/json'}
	response = requests.post('http://localhost:8083/connectors', data=contents, headers=headers)
	print "Kafka Connect response: " + str( response )

def waitForRecordsToArrive(numberOfEpectedMessages):
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
		amount = 0
		while (amount<numberOfEpectedMessages):
			msg = c.poll(0.1)
			if msg is None:
				continue
			elif not msg.error():
				amount += 1
#				print('Received {1}. message: {0}'.format(msg.value(), amount))

			elif msg.error().code() == KafkaError._PARTITION_EOF:
				print('End of partition reached {0}/{1}'
					  .format(msg.topic(), msg.partition()))
			else:
				print('Error occured: {0}'.format(msg.error().str()))

	except KeyboardInterrupt:
		pass

	finally:
		c.close()

number = 10000

print( "## Start Workflow Instances" )
start = time.clock()
startWorkflowInstances(number)
end = time.clock()
print( "Started "+str(number)+" workflow instances: " + str((end - start) * 1000) + ' milliseconds' );

print( "## Start Kafka Connect Source" )
start = time.clock()
startKafkaConnectSource()
end = time.clock()
print( "Started Source: " + str((end - start) * 1000) + ' milliseconds' );

print( "## Start Kafka Consumer to Check for Messages" )
start = time.clock()
waitForRecordsToArrive(number)
end = time.clock()
print( str(number) + " records arrived on topic 'pong' in Kafka: " + str((end - start) * 1000) + ' milliseconds' );