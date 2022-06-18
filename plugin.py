#! /usr/bin/env python3

import math
import re
import sys
import zipfile
from io import BytesIO
from os import path

import cv2
import numpy as np
from maubot import MessageEvent, Plugin
from maubot.handlers import event
from mautrix.types import EventType, MessageType
from mautrix.types.event.message import ImageInfo, MediaMessageEventContent
from PIL import Image

BASE_PATH = path.dirname(path.realpath(__file__))

question_regex = re.compile(r"an? (?P<noun>.+)\?")
command_regex = re.compile(r"\!perryfy ?(?P<noun>.*)")

image_event_map = {}


def load_resource(from_path: str):

    if BASE_PATH.endswith(".mbp"):
        with zipfile.ZipFile(BASE_PATH) as mbp:
            return mbp.open(from_path)
    return open(from_path, "rb")


def detect_object(src):
    image = cv2.imdecode(np.frombuffer(src.read(), np.uint8), cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    processed = cv2.erode(thresh.copy(), None, iterations=1)

    contours, _ = cv2.findContours(processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    largest_contour, *_ = sorted(contours, key=cv2.contourArea, reverse=True)

    circle = cv2.minEnclosingCircle(largest_contour)

    return circle


def perryfy(source):
    (obj_x, obj_y), object_radius = detect_object(source)

    img = Image.open(source)

    width, height = img.size

    # resize but retain aspect ratio
    hat = Image.open(load_resource("res/img/perryhat.png"))
    hat_orig_width, hat_orig_height = hat.size
    factor = max((0.3 * width) / hat_orig_width, (0.3 * height) / hat_orig_height)
    hat_width = math.floor(factor * hat_orig_width)
    hat_height = math.floor(factor * hat_orig_height)

    hat = hat.resize((hat_width, hat_height))

    # fudge position towards the top of the object
    hat_x = obj_x - 0.5 * hat_width
    hat_y = obj_y - 0.5 * hat_height

    hat_y -= 0.75 * object_radius

    hat_pos = (math.floor(hat_x), math.floor(hat_y))

    img.paste(hat, hat_pos, mask=hat)

    return img


class PerryfierPlugin(Plugin):
    @event.on(EventType.ROOM_MESSAGE)
    async def handler(self, evt: MessageEvent) -> None:
        content = evt.content

        # track most recent image event in a room
        if content.msgtype == MessageType.IMAGE:
            image_event_map[evt.room_id] = evt.event_id
            return

        if not content.msgtype.is_text:
            return

        salient_match = question_regex.match(content.body)
        if not salient_match:
            salient_match = command_regex.match(content.body)
        if not salient_match:
            return
        noun = salient_match.group("noun") or None

        await evt.mark_read()

        if evt.room_id not in image_event_map:
            return

        img_evt = await self.client.get_event(evt.room_id, image_event_map[evt.room_id])
        source_img_bytes = await self.client.download_media(img_evt.content.url)

        source_img = BytesIO()
        source_img.write(source_img_bytes)

        img = perryfy(source_img)

        await self.send_image(evt, img, noun)

    async def send_image(self, evt, img, noun=None):
        file = BytesIO()
        img.save(file, format="png")
        mxc_uri = await self.client.upload_media(file.getvalue(), mime_type="image/png")
        content = MediaMessageEventContent()
        info = ImageInfo()
        info.width, info.height = img.size
        info.mimetype = "image/png"
        content.info = info

        noun_portion = "" if noun is None else f"-the-{noun}"
        content.body = f"perry{noun_portion}.png"
        content.msgtype = "m.image"
        content.url = mxc_uri
        await evt.respond(content)


if __name__ == "__main__":
    print(sys.argv[1])
    with open(sys.argv[1], "rb") as test_file:
        perryfy(test_file).show()
