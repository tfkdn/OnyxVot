import discord
from .db_models import *
import asyncio
from .schedule import schedule


def is_ori_cute_present(st: str) -> bool:
    check = ["CUTE", "ORI", "FEMBOI", "FEMBOY", "FEMALE", "GIRLY", "CUTIE"]

    if any(item in st.upper() for item in
           check) and "NOT" not in st and "ORI" in st.upper() or "<@!242094224672161794>" in st:
        return True
    else:
        return False

def append_denaial(test_String, embed):
    if is_ori_cute_present(test_String):

        i_dont_give_a_fox = "https://media.discordapp.net/attachments/615192429615906838/716641148143272016" \
                            "/943fdf31aaab86c330beac1cb91e9a13.png "

        embed.description = f"{embed.description}\n`Even tho Ori definitely isn't and`"
        embed.set_image(url=i_dont_give_a_fox)

#
#
#

def usa_4th(cog, embed, msg):
    if cog.ct.month == 7 and cog.ct.day in [4, 5, 6]:
        us_starSprangled = "https://cdn.discordapp.com/attachments/615192429615906838/719389179007467520/653650594619326474.gif"
        embed.set_image(url=us_starSprangled)
        embed.description = f"{embed.description}\n`{msg}\nGod bless the United States of America`"

#
#
#

def VE_day(cog, embed, msg):
    if cog.ct.month == 5 and cog.ct.day in [8, 9, 10]:
        uk_union_Jack = "https://cdn.discordapp.com/attachments/615192429615906838/719566196890009600/665745198952742923.gif"
        embed.set_image(url=uk_union_Jack)
        embed.description = f"{embed.description}\n`{msg}\nGod save the Queen, God Save us all.`"

#
#
#

def in_memory_Thatcher(cog, embed, msg):
    if cog.ct.month == 4 and cog.ct.day in [8, 9, 10]:
        img_Thatcher = "https://media.discordapp.net/attachments/615192429615906838/722918618773454948/260px-Margaret_Thatcher_cropped2.png"
        embed.set_image(url=img_Thatcher)
        embed.description = f"{embed.description}\n`{msg}\nGod save the Queen, God Save us all.`"

#
#
#

async def doRemind(cog, rem: Reminder):
    """
    Sends reminder to user when ct coincides with time in a reminder,
    The dm also has a reaction that if reacted to within a timeout will remind again after the interval
    """
    user = cog.bot.get_user(rem.user_bind)

    e = discord.Embed(title=f"Reminder:",
                      description=f"{rem.desc}",
                      colour=cog.embed_colour)

    e.set_footer(text=f"React to be reminded again in {rem.time_differential}")

    append_denaial(rem.desc, embed=e)
    usa_4th(cog, embed=e, msg="Happy Independence day")
    VE_day(cog, embed=e, msg="Happy VE day")
    in_memory_Thatcher(cog, embed=e, msg="In loving memory of Margaret Thatcher.\nMay in peace she rest.")

    msg = await user.send(embed=e)


    # Adds reaction to previous msg

    reaction = await msg.add_reaction("🔁")

    def check(reaction, user):
        # print(reaction, user)
        # print(str(reaction.emoji) == "🔁" and reaction.count != 1)
        return str(reaction.emoji) == "🔁" and reaction.count != 1 and reaction.message.id == msg.id

    try:
        # print("Trying")
        reaction2, user = await cog.bot.wait_for('reaction_add', timeout=300, check=check)


    except asyncio.TimeoutError:
        # print("TimeOut Case")
        await msg.remove_reaction("🔁", msg.author)

        e.set_footer(text="")

        await msg.edit(embed=e)
        await rem.delete()
        cog.rem_total -= 1

    else:
        await Reminder.filter(rem_id=rem.rem_id).update(time_due_col=cog.ct + rem.time_differential)
        rem = await Reminder.filter(rem_id=rem.rem_id).first()

        await msg.add_reaction("✅")
        e.set_footer(text=f"Will remind again in {rem.time_differential}")
        await msg.edit(embed=e)

        cog.bot.loop.create_task(schedule(rem.time_due_col, doRemind, cog, rem), name=f"REMIND{rem.rem_id}")