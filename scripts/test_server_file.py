import httpx
import asyncio
import sys

async def test_file_access():
    base_url = "http://localhost:8000"
    
    # Paths to test
    paths = [
        "/media/local/douyin/7579916681788409339/video.mp4",
        "/media/douyin/7579916681788409339/video.mp4"
    ]
    
    async with httpx.AsyncClient() as client:
        # Check health first
        try:
            resp = await client.get(f"{base_url}/health")
            print(f"Health check: {resp.status_code}")
            if resp.status_code == 200:
                print(resp.json())
        except Exception as e:
            print(f"Server not reachable: {e}")
            return

        for path in paths:
            url = f"{base_url}{path}"
            print(f"\nTesting: {url}")
            try:
                resp = await client.head(url)
                print(f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"Content-Length: {resp.headers.get('content-length')}")
                    print("File is accessible!")
                else:
                    print("File NOT accessible.")
            except Exception as e:
                print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_file_access())
