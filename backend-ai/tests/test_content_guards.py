"""Guards merge_context / get_platform_spec (unittest, sans pytest-asyncio)."""

import asyncio
import unittest

from tools.content_generation.context_steps import (
    ContentPipelineState,
    get_platform_spec_step,
    merge_context_step,
)


class TestContentGuards(unittest.TestCase):
    def test_get_platform_spec_without_merge_raises(self):
        state = ContentPipelineState()
        with self.assertRaises(RuntimeError) as ctx:
            get_platform_spec_step(state, "instagram")
        self.assertIn("merge_context", str(ctx.exception).lower())

    def test_merge_then_spec_ok(self):
        async def _run():
            state = ContentPipelineState()
            await merge_context_step(
                state,
                idea_id=1,
                platform="instagram",
                brief={
                    "subject": "Sujet test",
                    "tone": "friendly",
                    "content_type": "feed_post",
                    "hashtags": True,
                    "include_image": True,
                    "call_to_action": None,
                },
                access_token=None,
            )
            return get_platform_spec_step(state, "instagram")

        spec = asyncio.run(_run())
        self.assertEqual(spec["platform"], "instagram")
        self.assertIn("max_caption_chars", spec)


if __name__ == "__main__":
    unittest.main()
