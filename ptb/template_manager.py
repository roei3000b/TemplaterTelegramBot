import boto3
from pathlib import Path
import uuid


class TemplateManager:
    def __init__(self):
        self.table_name = 'template'
        self.dynamodb = boto3.client('dynamodb')
        self.s3 = boto3.client('s3')
        self.bucket_name = "aws-sam-cli-managed-default-samclisourcebucket-jitqxwpiihk1"
        self.templates_table = self._get_or_create_template_table()

    def _get_or_create_template_table(self):
        try:
            self.dynamodb.describe_table(TableName=self.table_name)
            return boto3.resource('dynamodb').Table(self.table_name)
        except self.dynamodb.exceptions.ResourceNotFoundException:
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        'AttributeName': 'template_path',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'template_path',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 1,
                    'WriteCapacityUnits': 1
                }
            )

            # Wait until the table exists.
            table = boto3.resource('dynamodb').Table(self.table_name)
            table.wait_until_exists()
            return table

    def _generate_unique_key(self, file_name):
        unique_id = str(uuid.uuid4()).replace("-", "")
        return f"{unique_id}_{file_name}"

    def save(self, template_path, city, chat_id):
        key = self._generate_unique_key(Path(template_path).name)
        self.s3.upload_file(template_path, self.bucket_name, key)
        template_item = {
            'template_path': key,
            'city': city,
            'chat_id': chat_id
        }
        self.templates_table.put_item(Item=template_item)


    def list_templates(self):
        return self.templates_table.scan()["Items"]

    def delete(self, template_path):
        self.s3.delete_object(Bucket=self.bucket_name, Key=template_path)
        self.templates_table.delete_item(Key={'template_path': template_path})

    def delete_all(self):
        for template in self.list_templates():
            self.delete(template["template_path"])

