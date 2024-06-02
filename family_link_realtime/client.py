import asyncio
import socketio

sio_client = socketio.AsyncClient()


@sio_client.event
async def connect():
    print('socketio connected')


@sio_client.event
async def disconnect():
    print('socketio disconnected')


async def main():
    await sio_client.connect(url='http://localhost:3002', socketio_path='sockets')
    await sio_client.disconnect()

asyncio.run(main())
