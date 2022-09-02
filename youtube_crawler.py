import asyncio
import json
import os
import time
from typing import List

from pyppeteer import launch
from pyppeteer.page import Page
from pyppeteer_stealth import stealth

os.environ["PYPPETEER_CHROMIUM_REVISION"] = "975570"

INTERVAL = 2
RETRY_LIMIT = 10


async def stop_video_play(page: Page):
    await asyncio.sleep(2)

    player_status = await page.evaluate(
        "() => document.getElementById('movie_player').getPlayerState()"
    )

    if player_status == 1:
        await page.evaluate("{document.getElementById('movie_player').click()}")


async def to_bottom_of_page(page: Page):
    await page.evaluate(
        """{
            var height = document.getElementsByTagName("ytd-app")[0].scrollHeight;
            window.scrollBy(0, window.scrollBy(0, height));
        }"""
    )


async def extract_el(el):
    author_el = (
        await el.xpath(".//div[@id='header-author']//a[@id='author-text']/span")
    )[0]
    time_el = (
        await el.xpath(
            ".//yt-formatted-string[contains(@class, 'published-time-text')]/a"
        )
    )[0]
    content_el = (await el.xpath(".//div[@id='comment-content']//yt-formatted-string"))[
        0
    ]
    donation_els = await el.xpath(
        ".//yt-pdg-comment-chip-renderer/div/span[contains(text(), '$')]"
    )

    dict_ = {
        "author": (await (await author_el.getProperty("innerText")).jsonValue())
        .replace("\n", "")
        .strip(),
        "time": await (await time_el.getProperty("innerText")).jsonValue(),
        "content": await (await content_el.getProperty("innerText")).jsonValue(),
    }
    if donation_els:
        dict_["donation"] = (
            (await (await donation_els[0].getProperty("innerText")).jsonValue())
            .replace("$", "")
            .replace(",", "")
            .replace(" ", "")
        )

    return dict_


async def get_comments(page: Page) -> List:
    s_time = time.time()

    await to_bottom_of_page(page)
    total_el = await page.waitForXPath("//*[@id='count']/yt-formatted-string/span[1]")
    total = int(
        (await (await total_el.getProperty("innerText")).jsonValue()).replace(",", "")
    )

    target_xpath = "//ytd-comment-thread-renderer"
    count = len(await page.xpath(target_xpath))
    prev_count = 0

    retry_times = 0
    while count <= total and retry_times < RETRY_LIMIT:
        if count == prev_count:
            retry_times = retry_times + 1
        else:
            retry_times = 0

        await to_bottom_of_page(page)
        await asyncio.sleep(INTERVAL)
        prev_count = count
        count = len(await page.xpath(target_xpath))
        print(count)

    list_ = []
    comments = await page.xpath(target_xpath)
    for i in comments:
        list_.append(await extract_el(i))

    print(time.time() - s_time)
    return list_, True


async def main():
    video_id = "OnxxkBTlU8A"  # u can change video id here

    browser = await launch()
    try:
        page = await browser.newPage()
        await stealth(page)
        await page.setUserAgent(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4914.0 Safari/537.36"
        )

        await page.goto(f"https://www.youtube.com/watch?v={video_id}")
        await stop_video_play(page)
        await to_bottom_of_page(page)

        comments = await get_comments(page)
        with open("result.json", "w") as f:
            json.dump(comments, f)
    finally:
        await browser.close()


asyncio.run(main())

