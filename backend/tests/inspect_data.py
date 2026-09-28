import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

async def check():
    c = AsyncIOMotorClient(settings.MONGO_URI)
    db = c[settings.DB_NAME]
    workspaces = await db.workspaces.find().to_list(100)
    for ws in workspaces:
        wid = str(ws['_id'])
        fc = await db.feedback.count_documents({'workspace_id': wid})
        ins = await db.workspace_insights.find_one({'workspace_id': wid})
        owner = str(ws.get('owner_id', ''))
        print(f"WS: {ws.get('name')} (id={wid}, owner={owner}) -> feedback={fc}, has_insights={bool(ins)}")

if __name__ == '__main__':
    asyncio.run(check())
