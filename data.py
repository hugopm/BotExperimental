import boto3, json, os

class BotData:
    NB_PROBLEMS = 6
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb',
            aws_access_key_id = os.environ["AWS_ID"],
            aws_secret_access_key = os.environ["AWS_PASS"],
            region_name='eu-west-3')
        self.table = self.dynamodb.Table('bot-scores')
    def get_one(self, id):
        resp = self.table.get_item(
            Key = {'id': id}
        )
        item = resp['Item']
        sl = item['liste']
        return list(map(int, sl))
    
    def set_one(self, id, sl):
        print(f"Setting {id}")
        self.table.put_item(
            Item = {'id': id, 'liste': sl}
        )

    def delete(self, id):
        self.table.delete_item(Key = {'id': id})

    def scan(self):
        resp = self.table.scan()['Items']
        print(f"Scanned {len(resp)} items")
        return [[int(x['id']), list(map(int, x['liste']))] for x in resp]
