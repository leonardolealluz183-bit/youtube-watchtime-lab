import argparse
import asyncio
from playwright.async_api import async_playwright

SCENARIOS = {
    "engajado": [("play", 0), ("progress", 5), ("progress", 10), ("progress", 15), ("ended", 20)],
    "casual": [("play", 0), ("progress", 5), ("pause", 8)],
    "pula_trechos": [("play", 0), ("progress", 5), ("seek", 40), ("progress", 45), ("ended", 50)],
    "pausa_frequente": [("play", 0), ("pause", 3), ("play", 3), ("progress", 8), ("pause", 9), ("progress", 14)],
}

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--video-id", default="dQw4w9WgXcQ")
    args = parser.parse_args()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(args.base_url)
        for name, events in SCENARIOS.items():
            session = await page.request.post(f"{args.base_url}/api/sessions", data={"video_id": args.video_id, "video_duration": 50})
            sid = (await session.json())["id"]
            prev = 0
            for event_type, pos in events:
                await page.request.post(f"{args.base_url}/api/sessions/{sid}/events", data={"event_type": event_type, "position": pos, "previous_position": prev, "duration": 50, "meta": {"scenario": name}})
                prev = pos
        await browser.close()
    print("Simulações locais concluídas.")

if __name__ == "__main__":
    asyncio.run(main())
