import asyncio
import motor.motor_asyncio
import os
import bson

class ContestData:
    @classmethod
    async def factory(cls, cid):
        self = ContestData()
        conn_str = os.environ["MDB_URL"]
        self.client = motor.motor_asyncio.AsyncIOMotorClient(conn_str, serverSelectionTimeoutMS=5000)
        self.db = self.client.botexp
        self.con_obj_id = bson.ObjectId(cid)
        self.contest = await self.db.contests.find_one({"_id": self.con_obj_id})
        return self

    def get_name(self, i):
        return self.contest["problems"][i]
    
    @property
    def nb_problems(self):
        return len(self.contest["problems"])

    def get_filter(self, uid):
        return {
            "user" : uid,
            "contest": self.con_obj_id
        }

    async def get_scores(self, uid):
        resp = await self.db.results.find_one(self.get_filter(uid))
        if not resp:
            raise ValueError(f"{uid} not found in database")
        return resp["scores"]
    
    async def set_scores(self, uid, sl):
        print(f"Setting {uid}")
        await self.db.results.replace_one(
            self.get_filter(uid),
            {
                "user": uid,
                "scores": sl,
                "contest": self.con_obj_id
            }, upsert=True
        )

    async def delete(self, uid):
        result = await self.db.results.delete_one(self.get_filter(uid))
        return bool(result.deleted_count)

    async def get_all(self):
        cursor = self.db.results.find({"contest": self.con_obj_id})
        results = [[x["user"], x["scores"]] async for x in cursor]
        return results
