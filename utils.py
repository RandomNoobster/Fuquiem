import math
import discord
import asyncio

def embed_pager(title: str, fields: list, description: str = "", color: int = 0x00ff00, inline: bool = True) -> list:
        embeds = []
        for i in range(math.ceil(len(fields)/25)):
           embeds.append(discord.Embed(title=f"{title} page {i+1}", description=description, color=color)) 
        index = 0
        n = 0
        for field in fields:
            embeds[index].add_field(name=f"{field['name']}", value=field['value'], inline=inline)
            n += 1
            if n % 24 == 0:
                index += 1
        return embeds
                
async def reaction_checker(self, message: discord.Message, embeds: list) -> None:
    reactions = []
    for i in range(len(embeds)):
        reactions.append(asyncio.create_task(message.add_reaction(f"{i+1}\N{variation selector-16}\N{combining enclosing keycap}")))
    await asyncio.gather(*reactions)
    while True:
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=600)
            if user.bot == True or reaction.message != message:
                continue

            elif "\N{variation selector-16}\N{combining enclosing keycap}" in str(reaction.emoji):
                await message.edit(embed=embeds[int(str(reaction.emoji)[0])-1])
                await message.remove_reaction(reaction, user)

        except asyncio.TimeoutError:
            await message.edit(content="**Command timed out!**")
            break