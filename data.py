import boto3, json, os

class BotData:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id = os.environ["AWS_ID"],
            aws_secret_access_key = os.environ["AWS_PASS"])
        s3obj = self.s3.get_object(Bucket='botfrioi', Key='conf.json')["Body"]
        self.data = json.load(s3obj)
        print(self.data)
    def get(self, key):
        if not key in self.data.keys():
            self.data[key] = {}
        return self.data[key]
    def save(self):
        print("Saving..")
        print(self.data)
        self.s3.put_object(Bucket='botfrioi', Key='conf.json', Body=json.dumps(self.data))

if __name__ == "__main__":

    bd = BotData()
    sco = bd.get("scores")
    sco["hugopm"] = [40]*6
    sco["simon"] = [100]*6
    l = list(sco.items())
    l.sort(key = lambda x: -sum(x[1]))
    print(l)
    bd.save()
