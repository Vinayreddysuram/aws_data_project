import boto3
import json

# Initialize the StepFunctions client
client = boto3.client('stepfunctions')

def lambda_handler(event, context):

    stateMachineArn = 'arn:aws:states:us-east-1a:020368925103:stateMachine:GlueJobRunnerStateMachine'    
    # Start execution of the Step Function
    try:
        response = client.start_execution(
            stateMachineArn=stateMachineArn)
        print(response)
        return {
            'statusCode': 200,
            'body': json.dumps({'executionArn': response.get('executionArn')})
        }
    except client.exceptions.ClientError as error:
        # Log the error and return a 500 error code to the caller
        print(error)
        return {
            'statusCode': 500,
            'body': json.dumps({'errorMessage': str(error)})
        }
