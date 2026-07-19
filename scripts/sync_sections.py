#!/usr/bin/env python3
"""
Sync DEFAULT_SECTIONS content to the live database.
Overwrites existing section content with the latest defaults.
New sections (e.g. exp_arrise, projects) are created with correct ordering.

Usage:
    cd /opt/hemanth/portfolio
    python scripts/sync_sections.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, update
from app.database import async_session, engine, Base
from app.models import Section
from app.services.sections import DEFAULT_SECTIONS


async def sync_sections():
    async with async_session() as db:
        synced = 0
        created = 0

        for page, sections in DEFAULT_SECTIONS.items():
            for order, (key, data) in enumerate(sections.items()):
                result = await db.execute(
                    select(Section).where(Section.page == page, Section.section_key == key)
                )
                section = result.scalar_one_or_none()

                if section:
                    section.content = data["content"]
                    section.title = data["title"]
                    section.order = order
                    synced += 1
                    print(f"  updated  [{page}] {key}")
                else:
                    section = Section(
                        page=page,
                        section_key=key,
                        title=data["title"],
                        content=data["content"],
                        order=order,
                        visible=True,
                    )
                    db.add(section)
                    created += 1
                    print(f"  created  [{page}] {key}")

        await db.commit()
        print(f"\n✅ Done — {synced} updated, {created} created")


if __name__ == "__main__":
    asyncio.run(sync_sections())
