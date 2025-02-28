import globals as g


async def __get_all_msgs(from_id):
    msgs = []
    async for msg in g.app.iter_messages(from_id):
        msgs.append(msg.id)
    return msgs

async def clear_all(user_id):
    await g.app.delete_messages(
        g.CHANNEL_WITH_COMPLEXES,
        message_ids=await __get_all_msgs(g.CHANNEL_WITH_COMPLEXES)
    )
    await g.app.delete_messages(
        g.CHAT_WITH_RESULTS_ID,
        message_ids=await __get_all_msgs(g.CHAT_WITH_RESULTS_ID)
    )
    await g.app.delete_messages(
        user_id,
        message_ids=await __get_all_msgs(user_id)
    )