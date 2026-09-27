
from planet.requests.dispatch import Sync, Async
from planet.requests import data

get = data.GetSearch("f8737406627546c38f4db4bca5794bc6")

def doit():
    cl = Sync()
    print("respx.Response", cl.response(get))
    print("dict", cl.json(get))
    search = cl.data(get)
    print("search class", search)
    print(search.name, search.search_type)


async def doit_async():
    cl = Async()
    print("respx.Response", await cl.response(get))
    print("dict", await cl.json(get))
    search = await cl.data(get)
    print("search class", search)
    print(search.name, search.search_type)

if __name__ == "__main__":
    import asyncio, sys
    if sys.argv[1] == "sync":
        doit()
    else:
        asyncio.run(doit_async())