from typing import Iterator, Literal
from lib.utils import merge
from lib.capabilities.base import Capability


class UserActivity(Capability):
    def pull(
        self,
        username: str,
        max: int = None,
        until: str = None,
        type: Literal["posts", "comments", "likes"] = "posts",
    ) -> Iterator[dict]:
        """Pull the users' posts, comments, and likes from the API. Gettr groups all these different activities under the same API endpoint, so they are grouped here as well.

        :param str username: the username of the desired user
        :param int max: the maximum number of posts to pull
        :param str until: the earliest post ID to pull
        :param str type: whether to pull posts, comments, or likes"""

        assert type in ["posts", "comments", "likes"]

        url = f"/u/user/{username}/posts"
        n = 0  # Number of posts emitted

        # There is a fourth option, `f_u`, which for some users seems to return all their activity. It does not seem to work on all users, however.
        if type == "posts":
            fp_setting = "f_uo"
        elif type == "comments":
            fp_setting = "f_uc"
        elif type == "likes":
            fp_setting = "f_ul"

        for data in self.client.get_paginated(
            url,
            params={
                "max": 20,
                "dir": "fwd",
                "incl": "posts|stats|userinfo|shared|liked",
                "fp": fp_setting,
            },
            key="result",
        ):

            # Check if we've run out of posts to pull
            if len(data["data"]["list"]) == 0:
                break

            for event in data["data"]["list"]:
                id = event["activity"]["tgt_id"]

                # Information about posts is spread across three objects, so we merge them together here.
                post = merge(event, data["aux"]["post"][id], data["aux"]["s_pst"][id])

                # Verify that we haven't passed the `until` post
                if until is not None and until > id:
                    break

                # Verify that we haven't passed the max number of posts
                if max is not None and n >= max:
                    break

                n += 1
                yield post

            # Check if we've collected the maximum number of posts
            # Perhaps a duplicate of the above, but if we remove this check then we risk running forever when we run out of results
            if max is not None and max <= n:
                break