import logging
from pathlib import Path

from telethon.functions import stories
from telethon.types import (
    InputPrivacyValueAllowAll,
    InputPrivacyValueAllowUsers,
    InputUser,
    MessageMediaPhoto,
    User,
)

from envs import DEBUG, PUBLIC

from .base_thon import BaseThon


class Tagger(BaseThon):
    is_donor_good: bool = True

    def __init__(
        self,
        item: Path,
        json_file: Path,
        json_data: dict,
        fwd_from: str,
        usernames: set[str],
        fwd_index: int = 0,
        period: int | None = None,
    ):
        super().__init__(json_data)
        self.item, self.json_file = item, json_file
        self.fwd_from, self.fwd_index = fwd_from, fwd_index
        self.usernames = {u if u.startswith("@") else f"@{u}" for u in usernames}
        self.period = period

    async def __get_peer_stories(self) -> MessageMediaPhoto | None:
        try:
            result = await self.client(
                stories.GetPeerStoriesRequest(
                    peer=self.fwd_from  # type: ignore
                )
            )
            return result.stories.stories[self.fwd_index].media  # type: ignore
        except Exception as e:
            if DEBUG:
                logging.exception(e)

    async def __get_dialogs(self) -> set[str]:
        success_usernames = set()
        try:
            async for d in self.client.iter_dialogs():
                try:
                    if not d.is_user:
                        continue
                    username = str(d.entity.username)
                    if not username.startswith("@"):
                        username = f"@{username}"
                    if username in self.usernames:
                        success_usernames.add(username)
                except Exception as e:
                    if DEBUG:
                        logging.exception(e)
            return success_usernames
        except Exception as e:
            if DEBUG:
                logging.exception(e)
        return set()

    async def __get_input_privacy(
        self,
    ) -> InputPrivacyValueAllowUsers | InputPrivacyValueAllowAll:
        input_users = []
        for user in self.usernames:
            try:
                r = await self.client.get_entity(user)
                if not isinstance(r, User):
                    continue
                if r.id is not None and r.access_hash is not None:
                    input_users.append(InputUser(r.id, r.access_hash))
            except Exception as e:
                if DEBUG:
                    logging.exception(e)
        if PUBLIC:
            return InputPrivacyValueAllowAll()
        return InputPrivacyValueAllowUsers(input_users)

    async def __main(self, from_peer: MessageMediaPhoto) -> str:
        try:
            await self.client(
                stories.SendStoryRequest(
                    peer=await self.client.get_me(),  # type: ignore
                    media=from_peer,  # type: ignore
                    privacy_rules=[await self.__get_input_privacy()],
                    caption=" ".join(self.usernames),
                    period=None if not self.period else self.period,
                )
            )
            r = "|".join(await self.__get_dialogs())
            return f"OK:{r}"
        except Exception as e:
            if DEBUG:
                logging.exception(e)
            return "ERROR_STORY:Ошибка отправки сториса!"

    async def _main(self) -> str:
        r = await self.check()
        if "OK" not in r:
            return r

        # Get peer stories
        if not (from_peer := await self.__get_peer_stories()):
            await self.disconnect()
            return "ERROR_DONOR:Ошибка получения сторис у донора!"

        r = await self.__main(from_peer)
        await self.disconnect()
        return r

    async def main(self) -> str:
        r = await self._main()
        if "ERROR_DONOR" in r:
            Tagger.is_donor_good = False
        return r
