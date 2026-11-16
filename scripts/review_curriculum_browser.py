"""Review the real frontend in an isolated Firefox WebDriver BiDi session.

Optional QA tool: requires an already-running headless Firefox with a temporary
profile and the existing websockets dependency. Uses normal login and page JS.
Only a loopback preview origin is accepted. Screenshots contain no credentials.
"""

import argparse
import asyncio
import base64
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


async def run(args):
    from app.db.curriculum import load_curriculum
    from websockets.asyncio.client import connect
    from websockets.exceptions import ConnectionClosed

    marker = json.loads((args.directory / "preview.json").read_text())
    if (args.output / "browser-review.json").exists():
        raise ValueError("Refusing to overwrite a completed browser review")
    args.output.mkdir(parents=True, exist_ok=True)
    async with connect(args.bidi, max_size=40000000) as ws:
        serial = 0

        async def command(method, params):
            nonlocal serial
            serial += 1
            await ws.send(
                json.dumps({"id": serial, "method": method, "params": params})
            )
            while True:
                result = json.loads(await asyncio.wait_for(ws.recv(), 30))
                if result.get("id") == serial:
                    if result["type"] == "error":
                        raise RuntimeError(f"{method}: {result['error']}")
                    return result["result"]

        session = await command("session.new", {"capabilities": {}})
        try:
            tree = await command("browsingContext.getTree", {})
            context = tree["contexts"][0]["context"]

            async def evaluate(expression):
                result = await command(
                    "script.evaluate",
                    {
                        "expression": "JSON.stringify(" + expression + ")",
                        "target": {"context": context},
                        "awaitPromise": True,
                    },
                )
                if result["type"] != "success":
                    raise RuntimeError("Page script evaluation failed")
                return json.loads(result["result"].get("value", "null"))

            async def wait(expression):
                for _ in range(200):
                    try:
                        if await evaluate(expression):
                            return
                    except RuntimeError:
                        pass  # Navigation can replace the document/realm while polling.
                    await asyncio.sleep(0.1)
                raise RuntimeError("Page did not become ready: " + expression)

            async def navigate(path):
                await command(
                    "browsingContext.navigate",
                    {"context": context, "url": args.url + path, "wait": "complete"},
                )

            async def screenshot(name):
                # Existing page/tab reveal animations last up to 600 ms.
                await asyncio.sleep(0.8)
                shot = await command(
                    "browsingContext.captureScreenshot",
                    {
                        "context": context,
                        "origin": "document",
                        "format": {"type": "image/png"},
                    },
                )
                (args.output / (name + ".png")).write_bytes(
                    base64.b64decode(shot["data"])
                )

            async def layout():
                return await evaluate(
                    "({width: innerWidth, scrollWidth: "
                    "document.documentElement.scrollWidth, replacementCharacter: "
                    "document.body.innerText.includes('\\uFFFD')})"
                )

            await navigate("/login.html")
            await evaluate(
                "(()=>{document.getElementById('email').value="
                + json.dumps(marker["reviewer_email"])
                + ";document.getElementById('password').value="
                + json.dumps(marker["reviewer_password"])
                + ";document.getElementById('login-form').requestSubmit();return true})()"
            )
            await wait("location.pathname === '/dashboard.html'")
            content = load_curriculum()
            report = {
                "browser": session["capabilities"]["browserVersion"],
                "checks": [],
                "screenshots": [],
                "failures": [],
            }
            for label, width, height in [("desktop", 1440, 1000), ("mobile", 390, 844)]:
                await command(
                    "browsingContext.setViewport",
                    {
                        "context": context,
                        "viewport": {"width": width, "height": height},
                        "devicePixelRatio": 1,
                    },
                )
                await navigate("/courses.html")
                await wait("document.querySelectorAll('.catalog-card').length === 7")
                report["checks"].append(
                    {"page": "courses", "viewport": label, "layout": await layout()}
                )
                await screenshot("courses-" + label)
                for course in content.courses:
                    await navigate("/course.html?slug=" + course.slug)
                    await wait(
                        "document.querySelectorAll('.catalog-lesson-list a').length === 10"
                    )
                    links = await evaluate(
                        "Array.from(document.querySelectorAll("
                        "'.catalog-lesson-list a')).map(a=>a.getAttribute('href'))"
                    )
                    assert links == [
                        "/lesson.html?slug=" + lesson.slug for lesson in course.lessons
                    ]
                    report["checks"].append(
                        {
                            "page": course.slug,
                            "viewport": label,
                            "layout": await layout(),
                        }
                    )
                    if course.level == "A0":
                        await screenshot("course-a0-" + label)
                    for index, lesson in enumerate(course.lessons):
                        if index == 0:
                            await evaluate(
                                "(()=>{document.querySelector('.catalog-lesson-list a').click();"
                                "return true})()"
                            )
                        else:
                            await navigate(links[index])
                        await wait(
                            "document.getElementById('lesson-content').hidden === false"
                        )
                        await evaluate(
                            "(()=>{document.getElementById('tab-theory').click();"
                            "return true})()"
                        )
                        text = await evaluate(
                            "document.getElementById('panel-theory').innerText"
                        )
                        assert lesson.theory in text
                        assert all(example in text for example in lesson.examples)
                        assert all(
                            w.translation in text and w.word in text
                            for w in lesson.vocabulary
                        )
                        measurement = await layout()
                        if (
                            measurement["scrollWidth"] > width + 1
                            or measurement["replacementCharacter"]
                        ):
                            report["failures"].append(
                                {
                                    "lesson": lesson.slug,
                                    "viewport": label,
                                    "layout": measurement,
                                }
                            )
                        report["checks"].append(
                            {
                                "page": lesson.slug,
                                "viewport": label,
                                "theory": True,
                                "layout": measurement,
                            }
                        )
                        if index == 0:
                            await screenshot(f"{course.slug}-theory-{label}")
                    # Exercise form interaction on the last lesson in each course.
                    await evaluate(
                        "(()=>{document.getElementById('tab-practice').click();"
                        "return true})()"
                    )
                    spec = course.lessons[-1].exercises[0]
                    await evaluate(
                        "(()=>{const radio=Array.from(document.querySelectorAll("
                        "'#panel-practice input[type=radio]')).find(e=>e.value==="
                        + json.dumps(spec.correct_option_id)
                        + ");radio.click();"
                        "radio.closest('form').requestSubmit();return true})()"
                    )
                    await wait(
                        "document.querySelector('#panel-practice .lesson-feedback.is-correct') "
                        "!== null"
                    )
                    report["checks"].append(
                        {
                            "page": course.lessons[-1].slug,
                            "viewport": label,
                            "exercise_ui_correct": True,
                            "layout": await layout(),
                        }
                    )
                    if course.level == "B2":
                        await screenshot("exercise-b2-" + label)
                    # Real breadcrumb click back to course, then catalog.
                    await evaluate(
                        "(()=>{document.getElementById('lesson-course-link').click();"
                        "return true})()"
                    )
                    await wait(
                        "document.querySelectorAll('.catalog-lesson-list a').length === 10"
                    )
                    await evaluate(
                        "(()=>{document.querySelector('.catalog-breadcrumb a').click();"
                        "return true})()"
                    )
                    await wait(
                        "document.querySelectorAll('.catalog-card').length === 7"
                    )
                    print(
                        f"{label} {course.level}: 10 lessons, theory, words, exercise and navigation OK",
                        flush=True,
                    )
            for check in report["checks"]:
                measurement = check["layout"]
                if measurement["scrollWidth"] > measurement["width"] + 1:
                    report["failures"].append(check)
            report["screenshots"] = sorted(p.name for p in args.output.glob("*.png"))
            (args.output / "browser-review.json").write_text(
                json.dumps(report, indent=2) + "\n"
            )
            if report["failures"]:
                raise RuntimeError(
                    f"Layout failures: {len(report['failures'])}; see JSON"
                )
            print(
                f"PASS: {len(report['checks'])} page checks; {len(report['screenshots'])} screenshots"
            )
        finally:
            try:
                await command("session.end", {})
            except (RuntimeError, TimeoutError, ConnectionClosed):
                print("Browser session cleanup unavailable", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:3012")
    parser.add_argument("--bidi", default="ws://127.0.0.1:9227/session")
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if any(
        urlsplit(url).hostname not in {"127.0.0.1", "localhost"}
        for url in (args.url, args.bidi)
    ):
        parser.error("Only isolated loopback endpoints are allowed")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
